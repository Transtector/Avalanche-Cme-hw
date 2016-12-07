# cmehw package main entry

import sys, time

import Config

from Logging import Logger
from Avalanche import Avalanche
from RRD import RRD

def main(args=None):
	'''Main hardware loop'''

	if args is None:
		args = sys.argv[1:]

	Logger.info("Avalanche (Cme-hw) is rumbling...")

	spinners = "|/-\\"
	spinner_i = 0

	avalanche = Avalanche() # CME transducer bus initialization

	rrd = RRD() # round-robin database - stores channel data

	channels = [] # transducer channels 

	print("\n ---")

	while(True):
		start_time = time.time() # start of loop

		# Show Loop operation via Heartbeat LED
		avalanche.ledToggle(5)

		# start polling update by marking all channels stale
		for ch in channels:
			ch.stale = True

		# The updateSpiChannels() call on the avalanche object
		# updates all channels' sensor values to the latest readings.
		for i, hw_ch in enumerate(avalanche.updateSpiChannels()):
			# create or update a channel for each hardware channel found
			found = False

			# search channels cache for each hw_ch enumerated
			for ch in channels:
				# search current channels for hw_ch and clear
				# stale flag if found
				if id(ch) == id(hw_ch):
					# id() returns unique memory location of object
					# so works for checking equality
					found = True
					ch.stale = False
					break # break the loop leaving ch == current hw_ch

			if not found:
				# append the hw_ch as a new channel
				ch = hw_ch
				ch.id = 'ch' + str(i)
				ch.stale = False
				channels.append(ch)

			rrd.publish(ch) # ch is current hw_ch - publish its values


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
