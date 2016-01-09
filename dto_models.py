
import os, json

APPROOT = os.path.abspath(os.getcwd()) # /home/pi/Cme-hw
LOGDIR = os.path.join(APPROOT, 'log') # /home/pi/Cme-hw/log

# create the log directory if necessary
try:
	os.makedirs(LOGDIR)
except OSError as e:
	if e.errno != errno.EEXIST:
		raise

class Channel(dict):

	def __init__(self, index, timestamp, hw_sensors): 
		self['id'] = 'ch' + str(index)
		self['error'] = False

		self._stale = False
		self._logfile = os.path.join(LOGDIR, 'ch' + str(index) + '_log.json') 

		oldestSensorPoints = self._logInitialize(timestamp, hw_sensors)

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


	def updateSensors(self, timestamp, sensor_data):
		''' Assumes sensors array characteristics have not changed since init '''
		new_points = []
		for s in sensor_data:
			current_point = [ timestamp, s ]
			self['sensors']['data'][0] = current_point # current measurement point
			new_points.append(current_point)

		# append to log file
		with open(self._logfile, 'a') as f:
			f.write(json.dumps(new_points) + '\n')

		self._stale = False


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

### END DTO MODELS