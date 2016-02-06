import os, json, threading
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

		# log data and internal caches
		self.slog = ChannelDataLog(os.path.join(config.LOGDIR, id + '_sensors.json'), max_size=config.LOG_MAX_SIZE)
		#self.clog = ChannelDataLog(os.path.join(config.LOGDIR, id + '_controls.json'), max_size=config.LOG_MAX_SIZE)

		# dict keys that will get serialized for data transfers
		self['id'] = id
		self['error'] = hw_ch.error
		self['sensors'] = [ Sensor('s' + str(i), sensor.type, sensor.unit) for i, sensor in enumerate(hw_ch.sensors) ]
		self['controls'] = []

	def logSensors(self, timestamp):
		self['error'] = self.hw_ch.error

		self.newdata = [ s.value for s in self.hw_ch.sensors ]
		self.newdata.insert(0, timestamp)

		# append new sensor data entry to log file 
		# (this may push oldest data points out)
		if not self.hw_ch.error:
			self.slog.push(self.newdata)

		# read old sensor points from file as the
		# earliest point may have been dropped due
		# to log file size restrictions
		self.olddata = self.slog.peek() or self.newdata

	def publish(self, memcache_client):
		if not memcache_client or self.busy:
			return

		t = threading.Thread(target=self._publish, args=(memcache_client,))
		t.setDaemon(True)
		t.start()

	def _publish(self, memcache_client):

		self.busy = True
		
		# read a publishing config for this channel
		pub = json.loads(memcache_client.get(self.id + '_pub') or '{}')

		# clear log takes precedence
		if pub.get('reset', None): 
			# clear cache
			for s in self['sensors']:
				s['data'] = []
			self.slog.clear()

		# load history
		if pub.get('expand', None):

			# load entire file if cache is not bigger than the normal two points
			if not len(self['sensors'][0]['data']) > 2:

				# clear cache
				for s in self['sensors']:
					s['data'] = []

				for entry in self.slog.peekAll(): # [ [ timestamp0, sensor0_data, ..., sensorN_data ], ... ]
					for i in range(1, len(entry)):
						self['sensors'][i-1]['data'].append([ entry[0], entry[i] ])
			
			else:

				for i in range(1, len(self['sensors'])):
					self['sensors'][i-1]['data'].append([ self.newdata[0], self.newdata[i] ])
					if len(self['sensors'][i-1]['data']) > config.LOG_MAX_SIZE:
						self['sensors'][i-1]['data'] = self['sensors'][i-1]['data'][1:]

		# load oldest/newest data points only
		else: 			
			# fill the sensors' data arrays with the
			# oldest and newest data points.
			for i in range(1, len(self.newdata)):
				self['sensors'][i-1]['data'] = [
					[ self.olddata[0], self.olddata[i] ],
					[ self.newdata[0], self.newdata[i] ]
				]

		# publish this channel under 'chX' key
		memcache_client.set(self.id, json.dumps(self))

		# if necessary, update the channels list with
		# this channel id
		channels = json.loads(memcache_client.get('channels') or '[]')

		if not self.id in channels:
			channels.append(self.id)
			memcache_client.set('channels', json.dumps(channels))

		self.busy = False

class Sensor(dict):
	def __init__(self, id, sensorType, unit):
		self['id'] = id
		self['type'] = sensorType
		self['unit'] = unit
		self['data'] = []
