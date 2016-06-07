# main entry point for command line calling
import sys, time, json
import memcache
import config
import logging


from Avalanche import Avalanche
from Models import Dto_Channel


# configure app logging default logs to screen only if DEBUG set in config
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s [%(name)s] %(message)s',
							   datefmt='%Y-%m-%d %H:%M:%S')

# set format in default Flask logging StreamHandler for console (DEBUG) output
for h in logger.handlers:
	h.setFormatter(formatter)

# always send app log to file
fh = logging.handlers.RotatingFileHandler(config.APPLOG,
										  maxBytes=config.LOGBYTES,
										  backupCount=config.LOGCOUNT)
# increase level if DEBUG set
if config.DEBUG:
	fh.setLevel(logging.DEBUG)
else:
	fh.setLevel(logging.INFO)

# use same formatting for file
fh.setFormatter(formatter)
logger.addHandler(fh)

logger.info("Avalanche ({0}) is rumbling...".format(__name__))

def main(args=None):
	'''Main hardware loop'''

	if args is None:
		args = sys.argv[1:]


	# create shared memory object
	sharedmem = memcache.Client([config.MEMCACHE], debug=0)
	logger.info("Memcache {0} connected".format(config.MEMCACHE))

	# setup GPIO
	avalanche = Avalanche()

	# setup relay GPIO
	logger.info("Initializing relays...")
	avalanche.relayControl(1, True)
	avalanche.relayControl(2, True)
	avalanche.relayControl(3, True)
	avalanche.relayControl(4, True)

	logger.info("Sensor boards: Off")
	logger.info("SPI bus 0: Disabled")

	print("Discharging sensor caps - wait 10 seconds...")
	time.sleep(10);

	print("Sensor boards: On")
	avalanche.sensorPower(True)
	time.sleep(1);

	print("SPI bus 0: Enabled")
	avalanche.spiBus0isolate(False)

	print("Setup SPI devices")
	avalanche.setupSpiChannels(config.SPI_SENSORS)

	spinners = "|/-\\"
	spinner_i = 0

	dto_channels = []

	print("\n----")
	while(1):
		# Show Loop operation via Heartbeat LED
		avalanche.ledToggle(5)

		# synchronize - get timestamp for data points
		timestamp = avalanche.syncSensors()

		# Read hardware channels.  Channel sensor
		# value and control states are read into
		# the hw_channels list.
		# TODO: add support for hot-pluggable channels
		hw_channels = avalanche.readSpiChannels()

		# start by marking all dto_channels stale
		for ch in dto_channels:
			ch.stale = True

		# create or update a Dto_Channel for 
		# each hardware channel found
		for i, hw_ch in enumerate(hw_channels):
			found = False

			# search current dto_channels for hw_ch
			# and clear stale flag if found
			for dto_ch in dto_channels:
				# id() returns unique memory location of object
				# so works for checking equality
				if id(dto_ch.hw_ch) == id(hw_ch):
					found = True
					dto_ch.stale = False
					dto_ch.logSensors(timestamp)
					#dto_ch.setControls(timestamp, sharedmem)

			# if not found add as a new dto_channel
			if not found:
				dto_ch = Dto_Channel('ch' + str(i), hw_ch)
				dto_ch.logSensors(timestamp)
				#dto_ch.setControls(timestamp, sharedmem)
				dto_channels.append(dto_ch)

		# list of channels publishing data
		status_channels = json.loads(sharedmem.get('channels') or '[]')

		# remove stale channels from published data
		if any(ch for ch in dto_channels if ch.stale):
			for ch in dto_channels:
				if ch.stale:
					try:
						status_channels.remove(ch.id) # remove from channels list
					except:
						pass
					sharedmem.delete(ch.id) # remove channel
					sharedmem.delete(ch.id + "_pub") # remove channel publish config
		
		sharedmem.set('channels', json.dumps(status_channels))

		# drop stale channels
		dto_channels = [ch for ch in dto_channels if not ch.stale]

		# dto_channels now have new data which can be published
		for dto_ch in dto_channels:
			dto_ch.publish(sharedmem)

		# how long to finish loop?
		process_time = time.time() - timestamp

		# sleep until at least LOOP_PERIOD
		delay_time = 0
		if process_time < config.LOOP_PERIOD_s:
			delay_time = config.LOOP_PERIOD_s - process_time

		# read chX_pub's to display them in the console
		cc = ", ".join([ '%s:%s' % (ch, json.loads(sharedmem.get(ch + '_pub') or '{}')) for ch in status_channels ])

		# console output for peace of mind...
		msg = "Hardware looping [%.3f s, %.3f s] %s" % (process_time, delay_time, spinners[spinner_i])
		msg += "\t%s" % cc
	
		sys.stdout.write(msg + "\x1b[K\r") # "\x1b[k" is ANSII clear to end of line 
		sys.stdout.flush()
		spinner_i = (spinner_i + 1) % len(spinners)

		time.sleep(delay_time)

if __name__ == "__main__":
	main()
