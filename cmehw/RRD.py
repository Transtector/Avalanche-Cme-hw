import time, random
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
			"DS:index:GAUGE:300:0:100",
			"DS:random:GAUGE:300:0:100",
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
		ch_rrd = channel['id'] + '.rrd'

		try:
			ch_rrd_info = rrdtool.info(ch_rrd, "-d", config.RRDCACHED_ADDRESS)
		except:
			ch_rrd_info = None

		if not ch_rrd_info:
			# Channel RRD not found - create one.  One DS for every sensor in the channel.

			DS = []
			for s in channel['sensors']:
				# TODO: get the min/max sensor values from the sensor
				# and replace the "U" (unknowns) in the DS definition.
				DS.append("DS:" + s.id + ":GAUGE:300:U:U")

			# Add RRA's
			RRA = [ "RRA:LAST:0.5:1:{0}".format( 4 * 3600 ),	# every 1 second sample for 4 hours
				"RRA:AVERAGE:0.5:5m:{0}".format( 2 * 24 * 12 ),	# 5 minute min, max, and average for 2 days
				"RRA:MIN:0.5:5m:{0}".format( 2 * 24 * 12 ),
				"RRA:MAX:0.5:5m:{0}".format( 2 * 24 * 12 ),
				"RRA:AVERAGE:0.5:6h:{0}".format( 4 * 365 ) ]	# 6 hour average (4/day) for 1 year 

			rrdtool.create(ch_rrd, "-d", config.RRDCACHED_ADDRESS,
				"--step", "1", *(DS + RRA) )

			self._logger.info("RRD created for {0}".format(ch_rrd))

		# Update the channel's RRD
		DATA_UPDATE = "N:" + ":".join([ str(s.value) for s in channel['sensors'] ])
		rrdtool.update(ch_rrd, "-d", config.RRDCACHED_ADDRESS, DATA_UPDATE)

