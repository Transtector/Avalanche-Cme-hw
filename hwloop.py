#!./cme_hw_venv/bin/python

import RPi.GPIO as GPIO
import spidev
import time
import config
from drivers  import stpm3x    # TODO: rename
from drivers import avalanche
from stpm3x import STPM3X
import cmedata
import memcache

#create shared memory object
sharedmem = memcache.Client(['127.0.0.1:11211'], debug=0)
#initialize sharedmem object
sharedmem.set('status', cmedata.status)
print sharedmem

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


# setup sensor boards (== 'channels')
channels = [ stpm3x(spi0dev0), stpm3x(spi0dev1) ]

print 'Configuring %d channels:' % len(channels)

for i, channel in enumerate(channels):
	cfg = config.system['sensors'][i]

	print '\nChannel %d ...' % i

	for g in ['GAIN1', 'GAIN2']:
		
		if not g in cfg:
			print '    %s configuration missing' % g

	status = 0
	status |= channel.write(STPM3X.GAIN1, cfg['GAIN1'])
	status |= channel.write(STPM3X.GAIN2, cfg['GAIN2'])

	if not status:
		print '    error configuring channel %d' % i


'''
#sensor 1
cfg = config.system['sensors'][0]
#print(bin(cfg['GAIN1']))
print("#Sensors",len(config.system['sensors']))

if not 'GAIN1' in cfg:
	print("\nNo GAIN1 Configuration found")

status = 0

status |= sensor0.write(STPM3X.GAIN1, cfg['GAIN1'])
status |= sensor0.write(STPM3X.GAIN2, cfg['GAIN2'])

if not status == 0:
	print ("Error configuring sensor 0")


#sensor 2 configuration
cfg = config.system['sensors'][1]

status = 0
status |= sensor1.write(STPM3X.GAIN1, cfg['GAIN1'])
status |= sensor1.write(STPM3X.GAIN2, cfg['GAIN2'])

if not status == 0:
	print ("Error configuring sensor 1")
'''


print("\nLoop starting...")

while(1):

	# synchronize sensors - get timestamp for data points
	timestamp = avalanche.syncSensors()

	'''		
	v0 = sensor0.read(STPM3X.V2RMS)  * 0.035430    
	c0 = sensor0.gatedRead(STPM3X.C2RMS, 7) * 0.003333
	v1 = sensor0.read(STPM3X.V1RMS) * 0.035430 
	c1 = sensor0.gatedRead(STPM3X.C1RMS, 7) * 0.003333
	#v2 = sensor1.read(STPM3X.V2RMS)
	#c2 = sensor1.read(STPM3X.C2RMS)
	#v3 = sensor1.read(STPM3X.V1RMS)
	#c3 = sensor1.read(STPM3X.C1RMS)
	'''

	# reach each channels' sensors and update cme status
	for i, channel in enumerate(channels):
		cmedata.status['channels'][i]['sensors'][0]['data'][0] = [ timestamp, channel.read(STPM3X.V2RMS) * 0.035430 ]
		cmedata.status['channels'][i]['sensors'][1]['data'][0] = [ timestamp, channel.gatedRead(STPM3X.C2RMS, 7) * 0.003333 ]

	#update shared memory object
	sharedmem.set('status', cmedata.status)
	
	print '%f, %f' % (cmedata.status['channels'][0]['sensors'][0]['data'][0], 
					  cmedata.status['channels'][0]['sensors'][1]['data'][0])
	
	#print("V1RMS: " + str(v1) + " | C1RMS: " + str(c1))
	#print("V2RMS: " + str(v2) + " | C2RMS: " + str(c2))
	#print("V3RMS: " + str(v3) + " | C3RMS: " + str(c3))
	#print("V4RMS: " + str(v4) + " | C4RMS: " + str(c4))

	time.sleep(0.5)