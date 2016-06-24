import os, sys, time, random
import config
import rrdtool

TESTRRD = "test.rrd"

class RRD():

	def __init__(self):
		''' Verify connection to rrdcached on init
		'''
		from Logging import Logger

		self._logger = Logger # get main logger
		self._logger.info("Setting up RRD")

		start_time = time.time()

		rrdtool.create(TESTRRD,
			"-d", config.RRDCACHED_ADDRESS,
			"--step", "1", 
			"DS:index:GAUGE:10:0:100",
			"DS:random:GAUGE:10:0:100",
			"RRA:LAST:0.5:1:10")

		t = 0
		while (t < 10):
			rrdtool.update(TESTRRD,
				"-d", config.RRDCACHED_ADDRESS,
				"N:{0}:{1}".format(t, random.randint(0, 100)))
			t = t + 1
			time.sleep(1)

		# TODO: check the results (somehow).  If the RRD doesn't
		# init properly, then there's no point to continue (I think),
		# so we'd fire an exception and terminate the cmehw main program.
		self._test = rrdtool.fetch(TESTRRD,
			"-d", config.RRDCACHED_ADDRESS,
			"LAST",
			"--start", str(int(start_time)),
			"--end", str(int(time.time())))

		self._logger.info("RRD setup finished")


	def publish(self, channel):
		''' Publish channel data to an RRD.  Each sensor in the channel is assigned a DS (data source)
			in the RRD.
		'''
		# just return if channel is in error or stale
		if channel.error or channel.stale:
			return

		# use channel name to see if there's an existing RRD
		ch_rrd = channel.id + '.rrd'

		try:
			# use "-F" because we only want rrd header information - no flush necessary
			ch_rrd_exists = rrdtool.info(ch_rrd, "-d", config.RRDCACHED_ADDRESS, "-F")
		except:
			ch_rrd_exists = None

		# check for presence of "chX.rrd.reset" file
		ch_rrd_reset = os.path.isfile(os.path.join(config.LOGDIR, ch_rrd + '.reset'))

		if not ch_rrd_exists or ch_rrd_reset:
			# Channel RRD not found or reset requested - (re)create it.
			# One DS for every sensor in the channel.

			DS = []
			for s in channel.sensors:
				# TODO: get the min/max sensor values from the sensor
				# and replace the "U" (unknowns) in the DS definition.
				
				ds_name = ".".join([s.id, s.type. s.unit])
				
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

			rrdtool.create(ch_rrd, "-d", config.RRDCACHED_ADDRESS,
				"--step", "1", *(DS + RRA) )

			self._logger.info("RRD created for {0}".format(channel.id))

			if ch_rrd_reset:
				os.remove(os.path.join(config.LOGDIR, ch_rrd + '.reset'))
				if ch_rrd_exists:
					self._logger.info("RRD reset for {0}".format(channel.id))


		# Update the channel's RRD
		DATA_UPDATE = "N:" + ":".join([ "{:f}".format(s.value) for s in channel.sensors ])

		#self._logger.debug("RRD update: " + DATA_UPDATE) 

		# try/catch to watch out for updates that occur too often.  Here we just
		# log then ignore the exception (for now)
		try:
			rrdtool.update(ch_rrd, "-d", config.RRDCACHED_ADDRESS, DATA_UPDATE)

		except:
			self._logger.error(sys.exc_info()[1])
