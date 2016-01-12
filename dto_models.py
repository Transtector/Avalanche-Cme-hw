import os, json
import config

class Channel(dict):

	def __init__(self, index, timestamp, hw_sensors): 
		self['id'] = 'ch' + str(index)
		self['error'] = False

		self.stale = False
		self._logfile = os.path.join(config.LOGDIR, 'ch' + str(index) + '.json') 

		oldestSensorPoints = self._logInitialize(timestamp, hw_sensors)

		print "Channel[%d] - %d sensors, %d oldest points" %(index, len(hw_sensors), len(oldestSensorPoints))

		self['sensors'] = [ Sensor(i, sensor.type, sensor.unit, [ [ timestamp, sensor.value ], oldestSensorPoints[i] ]) for i, sensor in enumerate(hw_sensors) ]

	def _logInitialize(self, timestamp, hw_sensors):
		'''
		Open/create the channel log file and read the oldest sensor data points.
		If channel log file is created, the current sensor data points are
		written and returned.
		'''

		# Check the channel log for existing data
		if os.path.isfile(self._logfile) and os.path.getsize(self._logfile) > 0:
			with open(self._logfile, 'r') as f:
				oldest_points = json.loads(f.readline()) # first line of file

		else:
			oldest_points = [[ timestamp, sensor.value ] for sensor in hw_sensors]
			with open(self._logfile, 'w') as f:
				f.write(json.dumps(oldest_points) + '\n')

		return oldest_points


	def updateSensors(self, timestamp, hw_sensors):
		''' Assumes sensors array characteristics have not changed since init '''
		for i, s in enumerate(hw_sensors):
			self['sensors'][i]['data'][0] = [ timestamp, s.value ] # current measurement point

		# append to log file
		with open(self._logfile, 'a') as f:
			f.write(json.dumps([[ timestamp, s.value ] for s in hw_sensors]) + '\n')

		self.stale = False


class Sensor(dict):
	def __init__(self, index, sensorType, unit, initial_data_points):
		self['id'] = 's' + str(index)
		self['type'] = sensorType
		self['unit'] = unit
		
		# initialize data as two points [ timestamp, value ] in the list:
		#   data[0] => most recent sensor point
		#   data[1] => oldest sensor point
		# [ [ timestamp_recent, value_recent ],
		#   [ timestamp_oldest, value_oldest ] ]
		self['data'] = initial_data_points 
