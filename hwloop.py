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

# Setup status data transfer object (array of channels).
# This initializes as an empty list, but will get filled
# in the hw loop below.
status = { 'channels': [] }

class Channel(dict):
	def __init__(self, index, sensors): 
		self['id'] = 'ch' + str(index)
		self['sensors'] = sensors

	def updateSensors(self, timestamp, sensor_data):
		''' assumes sensors is same length as sensor_data '''
		for i, s in enumerate(self['sensors']):

			# First time through we add two spots to the data array
			# from the single measurement.  Subsequently we just
			# update the 0th element with the most current value.
			if len(s['data']) == 0:
				s['data'].append([ timestamp, sensor_data[i] ])
				s['data'].append([ timestamp, sensor_data[i] ]) # TODO: replace this w/data from log file
			else:
				s['data'][0] = [ timestamp, sensor_data[i] ] # current measurement point


class Sensor(dict):
	def __init__(self, index, sensorType, unit):
		self['id'] = 's' + str(index)
		self['type'] = sensorType
		self['unit'] = unit
		self['data'] = []


print("\nLoop starting...")
while(1):

	# synchronize sensors - get timestamp for data points
	timestamp = Avalanche.syncSensors()

	# read channel data
	ch_data = Avalanche.readSpiDevices()

	# process the channel data into points
	# ch_data = [ [ meas0, meas1, ..., measN ], ..., [ <each channel defined in Avalanche> ] ]
	for i, measurements in enumerate(ch_data):

		# TODO: update the channel log data

		# update cme channel status
		if i <= (len(status['channels']) - 1):
			ch = status['channels'][i]

		else:
			# Add a Sensor for every measurement in channel
			sensors = []
			for j, s in enumerate(Avalanche.getChannelSensorDefs(i)):
				sensors.append(Sensor(j, s.type, s.unit))

			ch = Channel(i, sensors)
			status['channels'].append(ch) # add to status object

		ch.updateSensors(timestamp, measurements)

	# update shared memory object
	sharedmem.set('status', json.dumps(status))

	#print 'status: %s\n\n' % json.loads(sharedmem.get('status'))

	time.sleep(config.system['loop_freq'])

