#!./cme_hw_venv/bin/python

import sys, time, json
import memcache
import config

from Avalanche import Avalanche
from Models import Dto_Channel

# create shared memory object
sharedmem = memcache.Client([config.MEMCACHE], debug=0)

# setup GPIO
Avalanche = Avalanche()

# setup relay GPIO
print("Initialize Relays")
Avalanche.relayControl(1, True)
Avalanche.relayControl(2, True)
Avalanche.relayControl(3, True)
Avalanche.relayControl(4, True)

print("Sensor boards: Off")
print("SPI bus 0: Disabled")

print("Discharging sensor caps - wait 10 seconds...")
time.sleep(10);             # give capacitors on sensors boards time to discharge

print("Sensor boards: On")
Avalanche.sensorPower(True)
time.sleep(1);

print("SPI bus 0: Enabled")
Avalanche.spiBus0isolate(False)

print("Setup SPI devices")
Avalanche.setupSpiChannels(config.SPI_SENSORS)

spinners = "|/-\\"
spinner_i = 0

dto_channels = []

print("\n----")
while(1):
	# Show Loop operation via Heartbeat LED
	Avalanche.ledToggle(5)

	# synchronize - get timestamp for data points
	timestamp = Avalanche.syncSensors()

	# Read hardware channels.  Channel sensor
	# value and control states are read into
	# the hw_channels list.
	# TODO: add support for hot-pluggable channels
	hw_channels = Avalanche.readSpiChannels()

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
	if process_time < config.LOOP_PERIOD_s:
		delay_time = config.LOOP_PERIOD_s - process_time
	else:
		delay_time = 0

	# read chX_pub's to display them in the console
	cc = ", ".join([ '%s:%s' % (ch, json.loads(sharedmem.get(ch + '_pub') or '{}')) for ch in status_channels ])

	# console output for peace of mind...
	msg = "Hardware looping [%.3f s, %.3f s] %s" % (process_time, delay_time, spinners[spinner_i])
	msg += "\t%s" % cc
	
	sys.stdout.write(msg + "\x1b[K\r") # "\x1b[k" is ANSII clear to end of line 
	sys.stdout.flush()
	spinner_i = (spinner_i + 1) % len(spinners)

	time.sleep(delay_time)
