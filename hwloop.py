#!./cme_hw_venv/bin/python

import time, json
import config, memcache

from drivers import Avalanche

#create shared memory object
sharedmem = memcache.Client(['127.0.0.1:11211'], debug=0)

# setup GPIO
Avalanche = Avalanche()

# setup relay GPIO
print("Initialize Relays")
Avalanche.relayControl(1, True)
Avalanche.relayControl(2, True)
Avalanche.relayControl(3, True)
Avalanche.relayControl(4, True)

print("Sensor boards: Off")
print("SPI bus 0: Disabled")

print("Please wait...")
time.sleep(10);             # give capacitors on sensors boards time to discharge

print("Sensor boards: On")
Avalanche.sensorPower(True)
time.sleep(1);

print("SPI bus 0: Enabled")
Avalanche.spiBus0isolate(False)

print("Setup SPI devices")
Avalanche.setupSpiDevices(config.system['sensors'])


class Channel(dict):
	def __init__(self, index, timestamp, hw_sensors): 
		self['id'] = 'ch' + str(index)
		self['error'] = False
		self._stale = False

		self['sensors'] = [ Sensor(i, sensor.type, sensor.unit, self._initSensorData(sensor)) for i, sensor in enumerate(hw_sensors) ]

	def _initSensorData(self, timestamp, hw_sensor):
		return [ [ timestamp, hw_sensor.value ], [ timestamp, hw_sensor.value ] ]


	def updateSensors(self, timestamp, sensor_data):
		''' Assumes sensors array characteristics have not changed since init '''
		for i, s in enumerate(self['sensors']):
			s['data'][0] = [ timestamp, sensor_data[i] ] # current measurement point

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


dto_channels = []

print("\nLoop starting...")
while(1):

	# Mark all DTO channels as stale.
	# We'll freshen the ones we actually read
	# the delete the stale ones in prep to grow
	# and shrink channels as their added/removed
	for ch in dto_channels:
		ch._stale = True

	# synchronize sensors - get timestamp for data points
	timestamp = Avalanche.syncSensors()

	# read channel data
	channels = Avalanche.readSpiDevices()

	# process Avalanche channels into DTO status channels
	for i, sensors in enumerate(channels):

		# Do we have this channel in our status DTO?
		# TODO: calculate a hash or some means to uniquely identify
		# the channel as configured with its sensors.  Currently
		# we aren't able to add/remove channels dynamically, but we'll
		# probably need to get there.
		if i <= (len(dto_channels) - 1):
			ch = dto_channels[i] # yes - update it

		else: # no - add it
			ch = Channel(i, sensors)
			dto_channels.append(ch)

		ch.updateSensors(timestamp, [ sensor.value for sensor in sensors ])
		ch['error'] = len([s for s in sensors if s.error]) != 0
		ch._stale = False

	# delete stale channels
	dto_channels = [c for c in dto_channels if not c._stale]

	# update shared memory object
	sharedmem.set('status', json.dumps({ 'channels': dto_channels }))
	#print 'status: %s\n\n' % json.loads(sharedmem.get('status'))

	time.sleep(config.system['loop_freq'])

