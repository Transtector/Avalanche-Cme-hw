import time, random
import config
import rrdtool

TESTRRD = "test.rrd"

class RRD():

	def __init__(self):
		''' Verify connection to rrdcached on init
		'''
		start_time = time.time()

		rrdtool.create(TESTRRD,
			"-d", config.RRDCACHED_ADDRESS,
			"--start", str(int(start_time - 1)),
			"--step", "1", 
			"DS:index:GAUGE:300:0:100",
			"DS:random:GAUGE:300:0:100",
			"RRA:LAST:0.5:1:10")

		t = 0
		while (t < 10):
			rrdtool.update(TESTRRD,
				"-d", config.RRDCACHED_ADDRESS,
				"N:{0}:{1}".format(t, random.randint(0,100)))
			t = t + 1
			time.sleep(1)

		self.test = rrdtool.fetch(TESTRRD,
			"-d", config.RRDCACHED_ADDRESS,
			"LAST",
			"--start", str(int(start_time)),
			"--end", str(int(time.time())))

	def publish(self, channel):
		pass
