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
			"--start", str(int(start_time)),
			"--step", "1", 
			"DS:random:GAUGE:2:0:100",
			"RRA:AVERAGE:0.5:1:10")

		t = 0
		while (t < 10):
			rrdtool.update(TESTRRD,
				"-d", config.RRDCACHED_ADDRESS,
				"{0}:{1}".format(int(time.time()), random.randint(0, 100)) )
			t = t + 1
			time.sleep(1)

		rrdtool.fetch(TESTRRD,
			"-d", config.RRDCACHED_ADDRESS,
			"AVERAGE",
			"--start", str(int(start_time)),
			"--end", str(int(time.time())))

	def publish(self, channel):
		pass