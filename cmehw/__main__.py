# cmehw package main entry

import sys, time

from .common import Config

from .Logging import Logger
from .Avalanche import Avalanche
from .RRD import RRD

from .Thresholds import ProcessAlarms

def main(args=None):
	'''Main hardware loop'''

	if args is None:
		args = sys.argv[1:]

	Logger.info("Avalanche (Cme-hw) is rumbling...")

	spinners = "|/-\\"
	spinner_i = 0

	avalanche = Avalanche() # CME transducer bus initialization

	rrd = RRD() # round-robin database - stores channel data

	print("\n ---")

	while(True):
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
		if process_time < Config.LOOP_PERIOD_s:
			delay_time = Config.LOOP_PERIOD_s - process_time

		# debug/print channel values
		#cc = "\n".join([ "{0}".format(ch.debugPrint()) for ch in channels ])
		#Logger.debug(cc)		
			
		# "\x1b[K" is ANSII clear to end of line
		sys.stdout.write("\tHardware looping [{0:.3f} s, {1:.3f} s] {2}\x1b[K\r".format(process_time, delay_time, spinners[spinner_i])) 
		sys.stdout.flush()
		spinner_i = (spinner_i + 1) % len(spinners)

		time.sleep(delay_time)

if __name__ == "__main__":
	try:
		main()

	except KeyboardInterrupt:
		Logger.info("Avalanche (Cme-hw) shutdown requested ... exiting")

	except Exception as e:
		Logger.info("Avalanche (Cme-hw) has STOPPED on exception {0}".format(e))

		# re-raise to print stack trace here (useful for debugging the problem)
		raise

	sys.exit(0)
