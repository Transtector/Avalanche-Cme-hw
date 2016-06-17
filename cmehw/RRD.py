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
		# use channel name to see if there's an existing RRD


		pass
