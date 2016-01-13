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
# For example, if the CME Channel 0 contains 2 sesors
# (1 voltage and 1 current), then the log file for that
# channel will look something like:
#
# ch0.json (filename shows that file data is json format compatible)
#   [[ 123000.789,   0.0 ], [ 123000.789, 0.000 ]] <-- oldest point, beginning of file
#   [[ 123100.789, 120.0 ], [ 123100.789, 0.500 ]]
#    ...
#   [[ 123100.789, 120.0 ], [ 123100.789, 0.500 ]] <-- newst point, end of file
#
# Data is appended to the channel file up to MAX_DATA_POINTS after
# which the oldest record is discarded when new records are added.
# This behavior works with the python queuelib ()
class Channel(dict):

	def __init__(self, index, error, timestamp, hw_sensors): 
		
		self['id'] = 'ch' + str(index)
		self['error'] = error
		self.stale = False

		self._log = ChannelDataLog(os.path.join(config.LOGDIR, 'ch' + str(index) + '_data.json'), max_size=config.LOG_MAX_SIZE)

		oldestPoints = self._log.peek()

		if not oldestPoints:
			oldestPoints = [[ timestamp, sensor.value ] for sensor in hw_sensors]

		#print "Channel[%d] - %d sensors, %d oldest points" %(index, len(hw_sensors), len(oldestSensorPoints))

		self['sensors'] = [ Sensor(i, sensor.type, sensor.unit, [ [ timestamp, sensor.value ], oldestSensorPoints[i] ]) for i, sensor in enumerate(hw_sensors) ]



	def updateSensors(self, error, timestamp, hw_sensors):
		''' Assumes sensors array characteristics have not changed since init '''
		self['error'] = error
		
		if not error:

			for i, s in enumerate(hw_sensors):
				self['sensors'][i]['data'][0] = [ timestamp, s.value ] # current measurement point

			# append sensor data to log file
			self._log.push([[ timestamp, s.value ] for s in hw_sensors])

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
