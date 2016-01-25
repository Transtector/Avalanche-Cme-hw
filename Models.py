import os, json
import config

from ChannelDataLog import ChannelDataLog


# DTO Channel model handles logging channel data 
# to file.  Each channel gets its own file in
# the LOGDIR found in the application config file.
# Channel data is logged as a single line per update
# which holds sensor data for every sensor in the
# channel (later we'll add channel control logging).
#
# For example, if the CME Channel 0 contains 2 sensors
# (1 voltage and 1 current), then the log file for that
# channel will look something like:
#
# ch0_sensors.json (filename shows that file data is json format compatible)
#   [ 123000.789,   0.0, 0.000 ] <-- oldest points, beginning of file
#   [ 123100.789, 120.0, 0.500 ]
#    ...
#   [ 123100.789, 120.0, 0.500 ] <-- newst points, end of file
#
# Data is appended to the channel file up to MAX_DATA_POINTS after
# which the oldest record is discarded when new records are added.
class Channel(dict):

	def __init__(self, id, error, timestamp, hw_sensors): 
		
		self['id'] = id
		self['error'] = error
		self.stale = False

		self._slog = ChannelDataLog(os.path.join(config.LOGDIR, id + '_sensors.json'), max_size=config.LOG_MAX_SIZE)
		#self._clog = ChannelDataLog(os.path.join(config.LOGDIR, id + '_controls.json'), max_size=config.LOG_MAX_SIZE)

		self['sensors'] = [ Sensor('s' + str(i), sensor.type, sensor.unit) for i, sensor in enumerate(hw_sensors) ]
		self['controls'] = []


	def updateSensors(self, error, timestamp, hw_sensors):
		''' Assumes sensors array characteristics have not changed since init '''
		self['error'] = error

		oldestPoints = []
		logdata = self._slog.peek() # [ timestamp, sensor0_data, ..., sensorN_data ]

		for i in range(1, len(logdata)):
			oldestPoints.append([ logdata[0], logdata[i] ]) # list of points: [ timestamp, sensor_data ], ...

		if not oldestPoints: # use current sensor values for oldest points
			oldestPoints = [[ timestamp, sensor.value ] for sensor in hw_sensors]

		for i, s in enumerate(hw_sensors):
			self['sensors'][i]['data'] = [ [ timestamp, s.value ], oldestPoints[i] ] 
		
		if not error:
			# append sensor data to log file (this may push oldest data points out)
			line = [s.value for s in hw_sensors]
			line.insert(0, timestamp)
			self._slog.push(line) # [ timestamp, sensor0_data, ..., sensorN_data ]

		self.stale = False


class Sensor(dict):
	def __init__(self, id, sensorType, unit):
		self['id'] = id
		self['type'] = sensorType
		self['unit'] = unit
		self['data'] = []
