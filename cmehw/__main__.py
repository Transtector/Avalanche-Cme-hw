# main entry point for command line calling
import sys, time, json

import config

from Logging import Logger
from Avalanche import Avalanche
from Models import Channel
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

		for i, hw_ch in enumerate(avalanche.updateSpiChannels()):
			# create or update a channel for each hardware channel found
			found = False

			for ch in channels:
				# search current channels for hw_ch and clear
				# stale flag if found
				if id(ch.hw_ch) == id(hw_ch):
					# id() returns unique memory location of object
					# so works for checking equality
					found = True
					ch.stale = False
					break # break the loop leaving ch == current hw_ch

			if not found:
				# add hw_ch as a new channel
				ch = Channel('ch' + str(i), hw_ch)
				channels.append(ch)

			rrd.publish(ch) # ch is current hw_ch - publish its values


		# how long to finish loop?
		process_time = time.time() - start_time

		# sleep until at least LOOP_PERIOD
		delay_time = 0
		if process_time < config.LOOP_PERIOD_s:
			delay_time = config.LOOP_PERIOD_s - process_time

		# debug/print channel values
		#cc = "\n".join([ "{0}".format(ch.debugPrint()) for ch in channels ])
		#Logger.debug(cc)		
			
		# "\x1b[K" is ANSII clear to end of line
		sys.stdout.write("\tHardware looping [{0:.3f} s, {1:.3f} s] {2}\x1b[K\r".format(process_time, delay_time, spinners[spinner_i])) 
		sys.stdout.flush()
		spinner_i = (spinner_i + 1) % len(spinners)

		time.sleep(delay_time)

if __name__ == "__main__":
	main()
