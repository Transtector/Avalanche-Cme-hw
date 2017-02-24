
from collections import deque
from .Thresholds import alarms

class Channel():

	def __init__(self, id):
		self.id = id
		self.error = False
		self.stale = False
		self.sensors = [ Sensor('s0') ]


class Sensor():
	def __init__(self, id):
		self.id = id
		self.values = deque([['NaN', 'NaN'] for x in range(5)])

	def update(self, point):
		self.values.appendleft( point ) # push onto buffer (left)
		self.values.pop() # remove oldest (right)

# WARNING: MAX 5

c = Channel('ch9')

def Test1():
	# no prior measurements yet made (first measured point)
	# Use 'EMPTY' classification (no prior alarms)
	c.sensors[0].update([ 0, 4 ]) # remaining buffer points are ["NaN", "NaN"]
	alarms(c)



def Test2():
	# no prior measurements
	# 'EMTPY' alarm history
	c.sensors[0].update([ 1, 5.1 ])
	alarms(c)


def Test3():
	# no prior measurements
	# 'EMTPY' alarm history
	# Add 5 alarm points
	for i, ap in enumerate(range(5)):
		c.sensors[0].update([ 2 + i, 5 + (i + 1) * 0.1 ])
		alarms(c)


def Test4():
	# uses Test3 'EMPTY' alarms
	# add 20 more points ramping down to no alarm
	for i, ap in enumerate(range(20)):
		c.sensors[0].update([ 7 + i, 5.5 - (i + 1) * 0.1 ])
		alarms(c)

def Test5():
	# uses Test4 'EMPTY' alarms
	# add 10 more points ramping up to alarm
	for i, ap in enumerate(range(10)):
		c.sensors[0].update([ 27 + i, 4.5 + (i + 1) * 0.1 ])
		alarms(c)

