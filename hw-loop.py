import RPi.GPIO as GPIO
import spidev
import time
import config
from drivers  import stpm3x    # TODO: rename
from stpm3x import STPM3X

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
sensor1 = stpm3x(spiDevice0)


cfg = config.system['sensors'][0]
#print(bin(cfg['GAIN1']))
print("#Sensors",len(config.system['sensors']))

if not 'GAIN1' in cfg:
    print("\nNo GAIN1 Configuration found")

status = 0

status |= sensor1.write(STPM3X.GAIN1, cfg['GAIN1'])
status |= sensor1.write(STPM3X.GAIN2, cfg['GAIN2'])

if not status == 0:
    print ("Error configuring sensor")




print("\nLoop Started...")

while(1):
    print("----")
    GPIO.output(12, GPIO.LOW)
    GPIO.output(13, GPIO.LOW)
    time.sleep(.001)
    GPIO.output(12, GPIO.HIGH)
    GPIO.output(13, GPIO.HIGH)

    v1 = sensor1.read(STPM3X.V1RMS)
    c1 = sensor1.read(STPM3X.C1RMS)
    
    print("V1RMS: " + str(v1) + " | C1RMS: " + str(c1))

    time.sleep(1)
    





