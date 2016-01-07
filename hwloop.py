#!./cme_hw_venv/bin/python

import RPi.GPIO as GPIO
import spidev
import time
import config
from drivers  import stpm3x    # TODO: rename
from drivers import avalanche
from stpm3x import STPM3X
import memcache

#create shared memory object
sharedmem = memcache.Client(['127.0.0.1:11211'], debug=0)

#Initialize SPI Devices
#setup SPI device 0
spi0dev0 = spidev.SpiDev()
spi0dev0.open(0, 0)   # TODO: read from config file
spi0dev0.mode = 3     # (CPOL = 1 | CPHA = 1) (0b11)

#setup SPI device 1
spi0dev1 = spidev.SpiDev()
spi0dev1.open(0, 1)   # TODO: read from config file
spi0dev1.mode = 3     # (CPOL = 1 | CPHA = 1) (0b11)

#setup GPIO
avalanche = avalanche()

#setup relay GPIO
print("Initialize Relays")
avalanche.relayControl(1, True)
avalanche.relayControl(2, True)
avalanche.relayControl(3, True)
avalanche.relayControl(4, True)

print("Sensor boards: Off")
print("SPI bus 0: Disabled")
print("Please wait...")
time.sleep(10);             #give capacitors on sensors boards time to discharge
print("Sensor boards: On")

avalanche.sensorPower(True)
time.sleep(1);
print("SPI bus 0: Enabled")
avalanche.spiBus0isolate(False)



# setup and configure sensor boards (== 'channels')
channels = [ stpm3x(spi0dev0) , stpm3x(spi0dev1) ]

print '\nConfiguring %d channels:' % len(channels)

for i, channel in enumerate(channels):
	cfg = config.system['sensors'][i]

	print '\nChannel %d ...' % i

	for g in ['GAIN1', 'GAIN2']:
		if not g in cfg:
			print '    %s configuration missing' % g

	status = 0
	status |= channel.write(STPM3X.GAIN1, cfg['GAIN1'])
	status |= channel.write(STPM3X.GAIN2, cfg['GAIN2'])

	if not status == 0:
		print '    error configuring channel %d' % i
	else:
		print '    done'



# Setup status data transfer object (array of channels).
# This initializes as an empty list, but will get filled
# in the hw loop below.
status = { 'channels': [] }

class Channel(dict):
	def __init__(self, index, sensors): 
		self['id'] = 'ch' + str(index)
		self['sensors'] = sensors

	def updateSensors(self, sensor_data):
		''' assumes sensors is same length as sensor_data '''
		for i, s in enumerate(self['sensors']):
			s['data'][0] = sensor_data[i]

	def __repr__(self):
		dictrepr = dict.__repr__(self)
		return '%s(%s)' % (type(self).__name__, dictrepr)


class Sensor(dict):
	def __init__(self, index, sensorType, unit, data):
		self['id'] = 's' + str(index)
		self['type'] = sensorType
		self['unit'] = unit
		self['data'] = [ data, data ]

	def __repr__(self):
		dictrepr = dict.__repr__(self)
		return '%s(%s)' % (type(self).__name__, dictrepr)


print("\nLoop starting...")
while(1):

	# synchronize sensors - get timestamp for data points
	timestamp = avalanche.syncSensors()

	# process the channels (sensor boards)
	for i, channel in enumerate(channels):

		# read each channel's sensors into current values
		v = channel.read(STPM3X.V2RMS) * 0.035430 # Vrms
		c = channel.gatedRead(STPM3X.C2RMS, 7) * 0.003333 # Arms

		# TODO: update the channel log data

		# update cme channel status
		if i <= (len(status['channels']) - 1):
			ch = status['channels'][i]

		else:
			s0 = Sensor(0, 'AC_VOLTAGE', 'Vrms', [ timestamp, v ])
			s1 = Sensor(1, 'AC_CURRENT', 'Arms', [ timestamp, c ])
			ch = Channel(i, [ s0, s1 ] )
			status['channels'].append(ch)

		ch.updateSensors([ [ timestamp, v], [ timestamp, c] ])

		#ch['sensors'][0]['data'][0] = [ timestamp, v ]
		#ch['sensors'][1]['data'][0] = [ timestamp, c ]


	# update shared memory object
	sharedmem.set('status', status)
	
	print '%f:  %f Vrms, %f Arms' % (status['channels'][0]['sensors'][0]['data'][0][0], 
									 status['channels'][0]['sensors'][0]['data'][0][1],
									 status['channels'][0]['sensors'][1]['data'][0][1])

	time.sleep(1)

