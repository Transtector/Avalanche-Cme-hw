import os, glob, sys, time, random

import rrdtool

import Config

TESTRRD = "test.rrd"

class RRD():

	def __init__(self):
		''' Verify connection to rrdcached on init
		'''
		from Logging import Logger

		self._logger = Logger # get main logger
		self._logger.info("Setting up RRD")

		start_time = time.time()

		rrdtool.create('/data/log/' + TESTRRD,
			"--step", "1", 
			"DS:index:GAUGE:10:0:100",
			"DS:random:GAUGE:10:0:100",
			"RRA:LAST:0.5:1:10")

		t = 0
		while (t < 10):
			rrdtool.update('/data/log/' + TESTRRD,
				"N:{0}:{1}".format(t, random.randint(0, 100)))
			t = t + 1
			time.sleep(1)

		# TODO: check the results (somehow).  If the RRD doesn't
		# init properly, then there's no point to continue (I think),
		# so we'd fire an exception and terminate the cmehw main program.
		self._test = rrdtool.fetch('/data/log/' + TESTRRD,
			"LAST",
			"--start", str(int(start_time)),
			"--end", str(int(time.time())))

		self._logger.info("RRD setup finished")


	def publish(self, channel):
		''' Publish channel data to an RRD.  Each sensor in the channel is assigned a DS (data source)
			in the RRD.

			Channel RRD's are created if necessary using the filename convention:

				chx(y)_<timestamp>.rrd

			where y is used if more than channels 0..9 and timestamp is from int(time.time()).

			Publish will recreate an (fresh/empty) RRD if the following 'reset' file found:

				chx(y).rrd.reset

			and the reset file will be deleted after new RRD created.
		'''

		# Just return if channel is in error or stale (means no RRD's are created if the 
		# channel starts out in error condition).
		if channel.error or channel.stale:
			return

		# Use glob to find existing RRD for chX (this might result in None)
		ch_rrd = glob.glob(os.path.join(Config.LOGDIR, channel.id + '_*.rrd'))

		if ch_rrd:
			ch_rrd = ch_rrd[0] # full path to first match


		# check for presence of "chX.rrd.reset" file
		ch_rrd_reset = os.path.isfile(os.path.join(Config.LOGDIR, channel.id + '.rrd.reset'))

		if ch_rrd_reset:
			# remove ch_rrd if it is present
			if ch_rrd:
				os.remove(ch_rrd)
				self._logger.info("RRD {0} removed to reset".format(os.path.basename(ch_rrd)))
				ch_rrd = None

			# remove the ch reset file			
			os.remove(os.path.join(Config.LOGDIR, channel.id + '.rrd.reset'))


		if not ch_rrd:
			# Channel RRD not found or was reset create it.
			# One DS for every sensor in the channel.

			# embed first publish time in the RRD filename
			ch_rrd = channel.id + '_' + str(int(time.time())) + '.rrd'

			DS = []
			for s in channel.sensors:
				# TODO: get the min/max sensor values from the sensor
				# and replace the "U" (unknowns) in the DS definition.
				
				# NOTE: from rrdtool.org that ds_name must be from 1 to
				# 19 characters long in the characters [a-zA-Z0-9_].
				ds_name = "_".join([ s.id, s.type, s.unit ])

				self._logger.info("RRD adding DS {0}".format(ds_name))
				
				DS.append("DS:" + ds_name + ":GAUGE:10:U:U")

			# Add RRA's (anticipating 400 point (pixel) outputs for plotting)
			RRA = [ 
				# real-time - every point for 2 hours (3600 points/hour)
				"RRA:LAST:0.5:1:{:d}".format( 2 * 3600 ),

				# daily - 5 minute stats for a day (12 5m blocks per hour)
				"RRA:AVERAGE:0.5:5m:{:d}".format( 12 * 24 ),
				"RRA:MIN:0.5:5m:{:d}".format( 12 * 24 ),
				"RRA:MAX:0.5:5m:{:d}".format( 12 * 24 ),

				# weekly - 30 minute stats for 7 days (48 30m blocks per day)
				"RRA:AVERAGE:0.5:30m:{:d}".format( 48 * 7 ),
				"RRA:MIN:0.5:30m:{:d}".format( 48 * 7 ),
				"RRA:MAX:0.5:30m:{:d}".format( 48 * 7 ),
 
				# monthly - 2 hour stats for 31 days (12 2h blocks per day)
				"RRA:AVERAGE:0.5:2h:{:d}".format( 12 * 31 ),
				"RRA:MIN:0.5:2h:{:d}".format( 12 * 31 ),
				"RRA:MAX:0.5:2h:{:d}".format( 12 * 31 ),

				# yearly - 1 day stats for 365 days
				"RRA:AVERAGE:0.5:1d:{:d}".format( 1 * 365 ),
				"RRA:MIN:0.5:1d:{:d}".format( 1 * 365 ),
				"RRA:MAX:0.5:1d:{:d}".format( 1 * 365 ) ]

			rrdtool.create('/data/log/' + ch_rrd,
				"--step", "1", *(DS + RRA) )

			self._logger.info("RRD created for {0}".format(channel.id))

		else:
			# ensure ch_rrd is filename only at this point
			ch_rrd = os.path.basename(ch_rrd)

		# Update the channel's RRD
		DATA_UPDATE = "N:" + ":".join([ "{:f}".format(s.value) for s in channel.sensors ])

		#self._logger.debug("RRD update: " + DATA_UPDATE) 

		# try/catch to watch out for updates that occur too often.  Here we just
		# log then ignore the exception (for now)
		try:
			rrdtool.update('/data/log/' + ch_rrd, DATA_UPDATE)

		except:
			self._logger.error(sys.exc_info()[1])
