import sys, os, json, threading
import config

from ChannelDataLog import ChannelDataLog

class Dto_Channel(dict):

	def __init__(self, id, hw_ch):
		
		# class attributes don't show up in the serialization
		# but get used for manipulations (finding, filtering, etc)
		self.id = id
		self.hw_ch = hw_ch
		self.stale = False
		self.busy = False

		self.newdata = [] # logSensors pushes new data onto this list
		self.olddata = None # this is the oldest point left in the data log (also updated in logSensors)

		# log data and internal caches
		self.slog = ChannelDataLog(os.path.join(config.LOGDIR, id + '_sensors.json'), max_size=config.LOG_MAX_SIZE)
		self.slogdata = None
		#self.clog = ChannelDataLog(os.path.join(config.LOGDIR, id + '_controls.json'), max_size=config.LOG_MAX_SIZE)
		#self.clogdata = None

		self.maxpoints = 201 # maximum number of points transferred via cache

		# dict keys that will get serialized for data transfers
		self['id'] = id
		self['error'] = hw_ch.error
		self['sensors'] = [ Sensor('s' + str(i), sensor.type, sensor.unit) for i, sensor in enumerate(hw_ch.sensors) ]
		self['controls'] = []
		self['reset'] = False


	def logSensors(self, timestamp):
		self['error'] = self.hw_ch.error

		newdata = [ s.value for s in self.hw_ch.sensors ]
		newdata.insert(0, timestamp)

		# append new sensor data entry to log file 
		# (this may push oldest data points out)
		if not self.hw_ch.error:
			self.slog.enqueue(newdata)

		# append new data to stack of data collected
		self.newdata.append(newdata)

		# read old sensor points from file as the
		# earliest point may have been dropped due
		# to log file size restrictions
		self.olddata = self.slog.dequeue(peek=True) or newdata

	def publish(self, memcache_client):
		if not memcache_client or self.busy: 
			return

		t = threading.Thread(target=_publish, args=(self, memcache_client))
		t.setDaemon(True)
		t.start()

class Sensor(dict):
	def __init__(self, id, sensorType, unit):
		self['id'] = id
		self['type'] = sensorType
		self['unit'] = unit
		self['data'] = []


def _decimate(input_array, target_size):
	N = len(input_array)
	
	if N <= target_size:
		return input_array

	if target_size == 2:
		return [ input_array[0], input_array[-1] ]
	
	if target_size == 1:
		return [ input_array[-1] ]

	d_factor = N // (target_size - 1)

	result = [input_array[i*d_factor if i*d_factor < N-1 else N-1] for i in range(target_size)]
	result[-1] = input_array[-1]
	return result


def _publish(channel, memcache_client):

	channel.busy = True
	
	# read a publishing config for this channel
	pub = json.loads(memcache_client.get(channel.id + '_pub') or '{}')

	# clear log takes precedence
	if pub.get('reset', None): 
		# clear cache
		for s in channel['sensors']:
			s['data'] = []
		channel.slogdata = None
		channel.slog.flush()
		channel['reset'] = True

		# remove 'reset' from the pub object once
		# we've done the reset.
		del pub['reset']
		memcache_client.set(channel.id + '_pub', json.dumps(pub))

	else:
		channel['reset'] = False

	# load history
	if pub.get('expand', None):

		# clear cache
		for s in channel['sensors']:
			s['data'] = []

		# load from file if not yet loaded
		if not channel.slogdata:
			channel.slogdata = channel.slog.flush(peek=True) # [ [ timestamp0, sensor0_data, ..., sensorN_data ], ... ]

		# file may have been empty - check again after loading
		if not channel.slogdata: 
			channel.slogdata = [ channel.olddata ]
		else:
			channel.slogdata[0] = channel.olddata

		newdata = channel.newdata # copy any newly arrived data from stack
		channel.newdata = [] # flush newly arrived data stack
		channel.slogdata.extend(newdata) # extend our cache w/new data

		# decimate the cached log data and load into DTO
		for entry in _decimate(channel.slogdata, channel.maxpoints):
			for i, s in enumerate(channel['sensors']):
				s['data'].append([ entry[0], entry[i+1] ])


	# load oldest/newest data points only
	else: 			
		
		channel.slogdata = None
		newdata = channel.newdata
		channel.newdata = []

		# fill the sensors' data arrays with the
		# oldest and newest data points.
		for i, s in enumerate(channel['sensors']):
			s['data'] = [
				[ channel.olddata[0], channel.olddata[i+1] ],
				[ newdata[-1][0], newdata[-1][i+1] ]
			]

	# publish this channel under 'chX' key
	memcache_client.set(channel.id, json.dumps(channel))

	# if necessary, update the channels list with
	# this channel id
	channels = json.loads(memcache_client.get('channels') or '[]')

	if not channel.id in channels:
		channels.append(channel.id)
		memcache_client.set('channels', json.dumps(channels))

	channel.busy = False
