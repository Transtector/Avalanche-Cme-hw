#!/usr/bin/python

import RPi.GPIO as GPIO
import spidev
import time
import config
from drivers  import stpm3x    # TODO: rename
from stpm3x import STPM3X
import cmedata
import memcache

#create shared memory object
sharedmem = memcache.Client(['127.0.0.1:11211'], debug=0)
#initialize sharedmem object
sharedmem.set('status', cmedata.status)
print sharedmem

#setup SPI device 0
spiDevice0 = spidev.SpiDev()
spiDevice0.open(0, 0)   # TODO: read from config file
spiDevice0.mode = 3     # (CPOL = 1 | CPHA = 1) (0b11)

#setup SPI device 1
spiDevice1 = spidev.SpiDev()
spiDevice1.open(0, 1)   # TODO: read from config file
spiDevice1.mode = 3     # (CPOL = 1 | CPHA = 1) (0b11)

#setup GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT, initial=GPIO.HIGH) # TODO: read from config file
GPIO.setup(13, GPIO.OUT, initial=GPIO.HIGH) # TODO: read from config file

#setup GPIO for STPM34 power and bus isolator
GPIO.setup(5, GPIO.OUT, initial=GPIO.HIGH)  #power  
GPIO.setup(6, GPIO.OUT, initial=GPIO.HIGH)  #output enable bus isolator
print("Sensor boards: Off")
print("SPI bus 0: Disabled")
print("Please wait...")
time.sleep(10);
print("Sensor boards: On")
GPIO.output(5, GPIO.LOW)
time.sleep(2);
print("SPI bus 0: Enabled")
GPIO.output(6, GPIO.LOW)


#setup sensor boards
sensor0 = stpm3x(spiDevice0)
sensor1 = stpm3x(spiDevice1)

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



print("\nLoop Started...")

while(1):
    timestamp = time.time()
    #print("Sync Time: " + str(timestamp))

    #synchronize sensors
    GPIO.output(12, GPIO.LOW)
    GPIO.output(13, GPIO.LOW)
    time.sleep(.001)
    GPIO.output(12, GPIO.HIGH)
    GPIO.output(13, GPIO.HIGH)

    #read back sensor data
    v0 = sensor0.read(STPM3X.V1RMS)
    c0 = sensor0.read(STPM3X.C1RMS)
    v1 = sensor0.read(STPM3X.V2RMS)
    c1 = sensor0.read(STPM3X.C2RMS)
    v2 = sensor1.read(STPM3X.V1RMS)
    c2 = sensor1.read(STPM3X.C1RMS)
    v3 = sensor1.read(STPM3X.V2RMS)
    c3 = sensor1.read(STPM3X.C2RMS)

    cmedata.status['channels'][0]['sensors'][0]['data'][0] = [timestamp, v0]
    cmedata.status['channels'][0]['sensors'][1]['data'][0] = [timestamp, c0]
    cmedata.status['channels'][1]['sensors'][0]['data'][0] = [timestamp, v1]
    cmedata.status['channels'][1]['sensors'][1]['data'][0] = [timestamp, c1]

    #update shared memory object
    sharedmem.set('status', cmedata.status)
    
    print(cmedata.status['channels'][0]['sensors'][0]['data'][0])
    
    #print("V1RMS: " + str(v1) + " | C1RMS: " + str(c1))
    #print("V2RMS: " + str(v2) + " | C2RMS: " + str(c2))
    #print("V3RMS: " + str(v3) + " | C3RMS: " + str(c3))
    #print("V4RMS: " + str(v4) + " | C4RMS: " + str(c4))

    time.sleep(0.5)
    
    





