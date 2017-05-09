# cmehw package main entry

import os, sys, time, signal

from .common import Config, Logging

from .Avalanche import Avalanche
from .RRD import RRD
from .Thresholds import ProcessAlarms
from .Alarms import AlarmManager

SHUTDOWN_FLAG = False
LOGGER = None


def cleanup(signum=None, frame=None):
	global SHUTDOWN_FLAG
	if SHUTDOWN_FLAG: # we've already received SIGTERM and set this
		return

	SHUTDOWN_FLAG = True # stop main loop
	LOGGER.info("Shutdown detected - cleaning up")


def main(args=None):
	'''Main hardware loop'''

	if args is None:
		args = sys.argv[1:]

	# Log to console/screen too
	CONSOLE_LOGGING = '--console' in args
	
	global LOGGER
	LOGGER = Logging.GetLogger('cmehw', {
		'REMOVE_PREVIOUS': True,
		'PATH': os.path.join(Config.PATHS.LOGDIR, 'cme-hw.log'),
		'SIZE': (1024 * 10),
		'COUNT': 1,
		'FORMAT': '%(asctime)s %(levelname)-8s [%(name)s] %(message)s',
		'DATE': '%Y-%m-%d %H:%M:%S',
		'LEVEL': 'DEBUG',
		'CONSOLE': CONSOLE_LOGGING
	})

	LOGGER.info("Avalanche (Cme-hw) is rumbling...")


	# SIGTERM signal handler - called at shutdown (see common/Reboot.py)
	# This lets us reboot/halt from other code modules without having
	# GPIO included in them.
	LOGGER.info("Listening for shutdown signals")
	signal.signal(signal.SIGTERM, cleanup)
	signal.signal(signal.SIGHUP, cleanup)

	spinners = "|/-\\"
	spinner_i = 0

	rrd = RRD() # round-robin database - stores channel data

	alarmManager = AlarmManager()

	avalanche = Avalanche(alarmManager) # CME transducer bus initialization

	#print("\n ---")

	while not SHUTDOWN_FLAG:
		start_time = time.time() # start of loop

		# The updateChannels() call on the avalanche object
		# updates all channels' sensor values to the latest readings.
		for ch in avalanche.updateChannels():
			rrd.publish(avalanche.Channels[ch])
			
		#ProcessAlarms(ch) # check channel for alarms - i.e., value crossed threshold

		# how long to finish loop?
		process_time = time.time() - start_time

		# sleep until at least LOOP_PERIOD
		delay_time = 0
		if process_time < Config.HARDWARE.LOOP_PERIOD_s:
			delay_time = Config.HARDWARE.LOOP_PERIOD_s - process_time

		# debug/print channel values
		#cc = "\n".join([ "{0}".format(ch.debugPrint()) for ch in channels ])
		#LOGGER.debug(cc)		
			
		# "\x1b[K" is ANSII clear to end of line
		#sys.stdout.write("\tHardware looping [{0:.3f} s, {1:.3f} s] {2}\x1b[K\r".format(process_time, delay_time, spinners[spinner_i])) 
		#sys.stdout.flush()
		spinner_i = (spinner_i + 1) % len(spinners)

		time.sleep(delay_time)


if __name__ == "__main__":
	try:
		main()

	except KeyboardInterrupt:
		LOGGER.info("Avalanche (Cme-hw) shutdown requested ... exiting")

	except Exception as e:
		LOGGER.info("Avalanche (Cme-hw) has STOPPED on exception {0}".format(e))

		# re-raise to print stack trace here (useful for debugging the problem)
		raise

	finally:
		cleanup()
