import RPi.GPIO as GPIO
import spidev
import time
from STPM3X import Stpm3x, STPM3X

#GPIO assignments
AVALANCHE_GPIO_SENSOR_POWER     = 5
AVALANCHE_GPIO_ISOLATE_SPI_BUS  = 6

AVALANCHE_GPIO_SYNC_SENSOR0     = 12
AVALANCHE_GPIO_SYNC_SENSOR1     = 13

AVALANCHE_GPIO_RELAY_CHANNEL1   = 28
AVALANCHE_GPIO_RELAY_CHANNEL2   = 29
AVALANCHE_GPIO_RELAY_CHANNEL3   = 30
AVALANCHE_GPIO_RELAY_CHANNEL4   = 31

AVALANCHE_GPIO_LED1 = 32
AVALANCHE_GPIO_LED2 = 33
AVALANCHE_GPIO_LED3 = 34
AVALANCHE_GPIO_LED4 = 35
AVALANCHE_GPIO_LED5 = 36

class Avalanche(object):

	class _Sensor:
		def __init__(self, sensor_type, unit, value, read):
			self.type = sensor_type
			self.unit = unit
			self.value = value
			self.read = read

	class _Channel:
		def __init__(self, device, error, sensors):
			self.device = device
			self.error = error
			self.sensors = sensors

	_Channels = [] # list of _Channel


	def __init__(self):
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)

		#initialize sensor sync pins
		GPIO.setup(AVALANCHE_GPIO_SYNC_SENSOR0, GPIO.OUT, initial=GPIO.HIGH) # TODO: read from config file
		GPIO.setup(AVALANCHE_GPIO_SYNC_SENSOR1, GPIO.OUT, initial=GPIO.HIGH) # TODO: read from config file

		#initialize relays
		GPIO.setup(AVALANCHE_GPIO_RELAY_CHANNEL1, GPIO.OUT, initial=GPIO.LOW)
		GPIO.setup(AVALANCHE_GPIO_RELAY_CHANNEL2, GPIO.OUT, initial=GPIO.LOW)
		GPIO.setup(AVALANCHE_GPIO_RELAY_CHANNEL3, GPIO.OUT, initial=GPIO.LOW)
		GPIO.setup(AVALANCHE_GPIO_RELAY_CHANNEL4, GPIO.OUT, initial=GPIO.LOW)

		#setup GPIO for STPM34 power and bus isolator
		GPIO.setup(AVALANCHE_GPIO_SENSOR_POWER, GPIO.OUT, initial=GPIO.HIGH)     #power
		GPIO.setup(AVALANCHE_GPIO_ISOLATE_SPI_BUS, GPIO.OUT, initial=GPIO.HIGH)  #output enable bus isolator

		#setup GPIO for LED Header
		GPIO.setup(AVALANCHE_GPIO_LED1, GPIO.OUT, initial=GPIO.LOW)     #LED 1
		GPIO.setup(AVALANCHE_GPIO_LED2, GPIO.OUT, initial=GPIO.LOW)     #LED 2
		GPIO.setup(AVALANCHE_GPIO_LED3, GPIO.OUT, initial=GPIO.LOW)     #LED 3
		GPIO.setup(AVALANCHE_GPIO_LED4, GPIO.OUT, initial=GPIO.LOW)     #LED 4
		GPIO.setup(AVALANCHE_GPIO_LED5, GPIO.OUT, initial=GPIO.LOW)     #LED 5

	def sensorPower(self, state):
		'''
		The sensor power bus is controlled via p-channel MOSFET. If output is High,
		bus power is off. If output is Low, power is sent to sensor bus.
		'''
		if state == True:
			outputState = GPIO.LOW
		else:
			outputState = GPIO.HIGH

		GPIO.output(AVALANCHE_GPIO_SENSOR_POWER, outputState)


	def spiBus0isolate(self, state):
		'''
		Bus isolator will isolate the bus if the output is high. The bus is
		enabled if the output is low.
		'''
		if state == True:
			outputState = GPIO.HIGH
		else:
			outputState = GPIO.LOW

		GPIO.output(AVALANCHE_GPIO_ISOLATE_SPI_BUS, outputState)


	def setupSpiChannels(self, config):
		'''
		Setup channels for each SPI device in config
		'''
		# for each SPI device (in config)
		for spi_device_index, spi_config in enumerate(config):

			# create a SpiDev for each sensor board
			spi = spidev.SpiDev()
			spi.open(0, spi_device_index) # TODO: read from config
			spi.mode = 3   # (CPOL = 1 | CPHA = 1) (0b11)

			# init stmp3x SPI device
			print "\nspi_device: %d" % (spi_device_index)
			device = Stpm3x(spi, spi_config)

			# add two channels for each stmp3x SPI device
			for channel_index in [0, 1]:

				# each SPI device channel has 2 sensors
				sensors = []

				# TODO: Read scale factors from config
				def v_read(spiDev, chIndex):
					v_read_param = STPM3X.V2RMS if (chIndex == 0) else STPM3X.V1RMS
					volts = spiDev.read(v_read_param) * 0.035484044
					#print "    %s Ch[%d].VOLTS = %f" % (str(spiDev._spiHandle), chIndex, volts)
					return volts

				def c_read(spiDev, chIndex):
					c_read_param = STPM3X.C2RMS if (chIndex == 0) else STPM3X.C1RMS
					amps = spiDev.gatedRead(c_read_param, 0) * 0.003429594
					#print "    %s Ch[%d].AMPS = %f" % (str(spiDev._spiHandle), chIndex, amps)
					return amps

				print "    Ch[%d] adding 2 sensors:" % (channel_index)

				sensors.append(self._Sensor('AC_VOLTAGE', 'Vrms', 0, lambda d=device, i=channel_index: v_read(d, i)  ))
				sensors.append(self._Sensor('AC_CURRENT', 'Arms', 0, lambda d=device, i=channel_index: c_read(d, i)  ))

				# save SPI device channels, their error state, and array of sensors
				self._Channels.append(self._Channel(device, device.error, sensors))


	def readSpiChannels(self):
		'''
		Runs through each channel's sensors and reads updated values
		'''
		for i, ch in enumerate(self._Channels):
			# update sensor values
			if not ch.error:
				for s in ch.sensors:
					s.value = s.read()

		return self._Channels

	def ledToggle(self, led):
		'''
		LEDs are controlled through an N Channel MOSFET.
		If GPIO output = low then LED = off,
		If GPIO output = high then LED = on
		'''
		if led == 1:
			ledState = not GPIO.input(AVALANCHE_GPIO_LED1)
			GPIO.output(AVALANCHE_GPIO_LED1, ledState)
		elif led == 2:
			ledState = not GPIO.input(AVALANCHE_GPIO_LED2)
			GPIO.output(AVALANCHE_GPIO_LED2, ledState)
		elif led == 3:
			ledState = not GPIO.input(AVALANCHE_GPIO_LED3)
			GPIO.output(AVALANCHE_GPIO_LED3, ledState)
		elif led == 4:
			ledState = not GPIO.input(AVALANCHE_GPIO_LED4)
			GPIO.output(AVALANCHE_GPIO_LED4, ledState)
		elif led == 5:
			ledState = not GPIO.input(AVALANCHE_GPIO_LED5)
			GPIO.output(AVALANCHE_GPIO_LED5, ledState)

	def ledControl(self, led, state):
		'''
		LEDs are controlled through an N Channel MOSFET.
		If GPIO output = low then LED = off,
		If GPIO output = high then LED = on
		'''
		if state == True:
			ledState = GPIO.HIGH
		else:
			ledState = GPIO.LOW

		if led == 1:
			GPIO.output(AVALANCHE_GPIO_LED1, ledState)
		elif led == 2:
			GPIO.output(AVALANCHE_GPIO_LED2, ledState)
		elif led == 3:
			GPIO.output(AVALANCHE_GPIO_LED3, ledState)
		elif led == 4:
			GPIO.output(AVALANCHE_GPIO_LED4, ledState)
		elif led == 5:
			GPIO.output(AVALANCHE_GPIO_LED5, ledState)

	def relayControl(self, channel, state):
		'''
		Relays are SPST. If the output is high, the relay will close its normally
		open contact
		'''
		if state == True:
			relayState = GPIO.HIGH
		else:
			relayState = GPIO.LOW

		if channel == 1:
			GPIO.output(AVALANCHE_GPIO_RELAY_CHANNEL1, relayState)
		elif channel == 2:
			GPIO.output(AVALANCHE_GPIO_RELAY_CHANNEL2, relayState)
		elif channel == 3:
			GPIO.output(AVALANCHE_GPIO_RELAY_CHANNEL3, relayState)
		elif channel == 4:
			GPIO.output(AVALANCHE_GPIO_RELAY_CHANNEL4, relayState)

	def syncSensors(self):
		'''
		STPM3X sensors can be sync'd by briefly pulling the sync line Low for
		each sensor board.
		'''
		GPIO.output(AVALANCHE_GPIO_SYNC_SENSOR0, GPIO.LOW)
		GPIO.output(AVALANCHE_GPIO_SYNC_SENSOR1, GPIO.LOW)
		time.sleep(0.001)
		GPIO.output(AVALANCHE_GPIO_SYNC_SENSOR0, GPIO.HIGH)
		GPIO.output(AVALANCHE_GPIO_SYNC_SENSOR1, GPIO.HIGH)

		return time.time()
