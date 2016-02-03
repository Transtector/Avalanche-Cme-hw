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
		self.id = id
		self['error'] = error
		self.stale = False

		self._slog = ChannelDataLog(os.path.join(config.LOGDIR, id + '_sensors.json'), max_size=config.LOG_MAX_SIZE)
		#self._clog = ChannelDataLog(os.path.join(config.LOGDIR, id + '_controls.json'), max_size=config.LOG_MAX_SIZE)

		self['sensors'] = [ Sensor('s' + str(i), sensor.type, sensor.unit) for i, sensor in enumerate(hw_sensors) ]
		self['controls'] = []


	def updateSensors(self, error, timestamp, hw_sensors, config={}):
		''' Assumes sensors array characteristics have not changed since init '''
		self['error'] = error

		# clear log file takes precedence
		if config.get('reset', None): 
			self._slog.clear()

		# retrieve decimated log data if expand=True
		if config.get('expand', None):
			logdata = self._slog.peekAll(max_points=201) # [ [ timestamp0, sensor0_data, ..., sensorN_data ], ... ]

		# else just retrieve the oldest point (first line) of log data
		else:
			logdata = [ self._slog.peek() ] # [ [ timestamp0, sensor0_data, ..., sensorN_data ] ]

		# if we haven't got any log data (yet) add the current sensor points
		if not logdata:
			logdata = [ [ s.value for s in hw_sensors ] ]
			logdata[0].insert(0, timestamp)

		# add the current sensor points (this will duplicate the first row if no log data yet)
		logdata.append([ s.value for s in hw_sensors ])
		logdata[-1].insert(0, timestamp)

		# append new sensor data to log file (this may push oldest data points out)
		if not error:
			self._slog.push(logdata[-1]) 

 		# clear existing sensor['data'] in prep for new data
		for i in range(len(self['sensors'])):
			self['sensors'][i]['data']=[]
		
		# At this point we have logdata as a 2D table of entries with at least two entries:
		#
		# logdata = [ 
		#	[ timestamp0, s0_data0, ..., sN_data0 ], 
		#		...,
		#	[ timestampM, s0_dataM, ..., sN_dataM ] 
		# ]
		#
		# However, sensors' 'data' are expecting a 2D array of data point pairs [timestamp, data], so
		# we build the data arrays from logdata for each sensor in the log entries
		for entry in logdata:
			for i in range(1, len(entry)):
				self['sensors'][i-1]['data'].append([ entry[0], entry[i] ])
		
		# channel is no longer considered 'stale'
		self.stale = False


class Sensor(dict):
	def __init__(self, id, sensorType, unit):
		self['id'] = id
		self['type'] = sensorType
		self['unit'] = unit
		self['data'] = []
