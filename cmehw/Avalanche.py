import os, time, glob, json

import RPi.GPIO as GPIO
import spidev

import Config

# load the STPM3X module and import Stpm3x class
from STPM3X import Stpm3x


# GPIO assignments
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


# Discharge sensors for this long before enabling SPI bus
SPI_BUS_DISCHARGE_WAIT_s = 10

# Hardware channels configurations stored here
CHDIR = Config.CHDIR

class Avalanche(object):

	class _Sensor:
		def __init__(self, id, sensor_type, unit, range, read_function):
			self.id = id
			self.type = sensor_type
			self.unit = unit
			self.range = range
			self._read = read_function

			self.value = 0

		def read(self):
			self.value = self._read()
			return self.value


	class _Channel:
		def __init__(self, bus_type, bus_index, bus_device_index, error, sensors):
			self.bus_type = bus_type
			self.bus_index = bus_index
			self.bus_device_index = bus_device_index
			self.error = error
			self.sensors = sensors


	_Channels = [] # list of _Channel


	def __init__(self):

		from Logging import Logger

		self._logger = Logger # get main logger
		self._logger.info("Setting up GPIO")

		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)

		# initialize sensor sync pins
		GPIO.setup(AVALANCHE_GPIO_SYNC_SENSOR0, GPIO.OUT, initial=GPIO.HIGH) # TODO: read from config file
		GPIO.setup(AVALANCHE_GPIO_SYNC_SENSOR1, GPIO.OUT, initial=GPIO.HIGH) # TODO: read from config file

		# initialize relays
		GPIO.setup(AVALANCHE_GPIO_RELAY_CHANNEL1, GPIO.OUT, initial=GPIO.LOW)
		GPIO.setup(AVALANCHE_GPIO_RELAY_CHANNEL2, GPIO.OUT, initial=GPIO.LOW)
		GPIO.setup(AVALANCHE_GPIO_RELAY_CHANNEL3, GPIO.OUT, initial=GPIO.LOW)
		GPIO.setup(AVALANCHE_GPIO_RELAY_CHANNEL4, GPIO.OUT, initial=GPIO.LOW)

		# setup GPIO for STPM34 power and bus isolator
		GPIO.setup(AVALANCHE_GPIO_SENSOR_POWER, GPIO.OUT, initial=GPIO.HIGH)     #power
		GPIO.setup(AVALANCHE_GPIO_ISOLATE_SPI_BUS, GPIO.OUT, initial=GPIO.HIGH)  #output enable bus isolator

		# setup GPIO for LED Header
		GPIO.setup(AVALANCHE_GPIO_LED1, GPIO.OUT, initial=GPIO.LOW)     #LED 1
		GPIO.setup(AVALANCHE_GPIO_LED2, GPIO.OUT, initial=GPIO.LOW)     #LED 2
		GPIO.setup(AVALANCHE_GPIO_LED3, GPIO.OUT, initial=GPIO.LOW)     #LED 3
		GPIO.setup(AVALANCHE_GPIO_LED4, GPIO.OUT, initial=GPIO.LOW)     #LED 4
		GPIO.setup(AVALANCHE_GPIO_LED5, GPIO.OUT, initial=GPIO.LOW)     #LED 5

		# setup relay GPIO
		self._logger.info("Initializing relay control")
		
		self.relayControl(1, True)
		self.relayControl(2, True)
		self.relayControl(3, True)
		self.relayControl(4, True)

		self._logger.info("Sensor boards: Off")
		self._logger.info("SPI bus 0: Disabled")

		self._logger.info("Discharging SPI bus caps - wait {0} seconds...".format(SPI_BUS_DISCHARGE_WAIT_s))
		time.sleep(SPI_BUS_DISCHARGE_WAIT_s);

		self._logger.info("Sensor boards: On")
		self.sensorPower(True)
		time.sleep(1);

		self._logger.info("SPI bus 0: Enabled")
		self.spiBus0isolate(False)

		self._logger.info("Setup SPI devices")
		self.setupChannels()


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


	def setupSpiChannel(self, spi_config, sensors):

		# configure based on device type
		device_type = spi_config['device_type']

		if device_type == 'STPM3X':

			# setup a new SPI channel using a STPM3X device
			spi_bus = spi_config['spi_bus']
			spi_device = spi_config['spi_device']
			
			# configure bus
			spi = spidev.SpiDev()
			spi.open(spi_bus, spi_device)
			spi.mode = 3 # (CPOL = 1 | CPHA = 1) (0b11)

			# Create an STPM3X device object on the SPI bus and pass the configuration.
			# See the STPM3X and Config class in the same module for configuration keys that
			# can be set here to override the defaults in the module.
			stpm3x = Stpm3x(spi, spi_config)

			# Construct a list of sensors for which we have configuration objects (passed in on sensors)
			_sensors = []

			for i, s in enumerate(sensors):

				s_config = s['_config'].copy()

				# There are some constraints on the sensor type and units as these strings
				# are used to construct the RRD data stream attributes.  For now, we have
				# type = [ "VAC", "CAC"] for AC RMS voltage, and AC RMS current types with
				# corresponding units = [ "Vrms", "Arms"] for RMS volts and amps.
				s_type = s_config['type']
				s_units = s_config['units']
				s_range = s_config.get('range', [])

				# Note that the sensor SCALE factor is set during device
				# calibration.  Here are a few scale factors we used for
				# various configurations:
				#
				#	0.035484044 : voltage scale for EVALSTPM34 board (AC Edge demo)
				#	0.056499432 : voltage scale for Optimus first proof-of-concept demo
				#	0.003429594 : current scale for AC Edge and Optimus POC
				s_register = s_config['register']
				s_scale = s_config['scale']
				s_threshold = s_config.get('threshold', None)

				# The STPM3X sensor read function as a closure to
				# capture register, scale, and threshold config
				def s_read(register, scale, threshold):

					def r():
						v = stpm3x.read(register, threshold) * scale
						print "\t{0} (scale: {1}, threshold: {2}) = {3}".format(register, scale, threshold, v)
						return v

					return r

				# Add the sensor the the _sensors for the Channel
				_sensors.append(self._Sensor('s' + str(i), s_type, s_units, s_range, s_read(s_register, s_scale, s_threshold)))

				self._logger.info("\tSTPMX3 device sensor added (register: {0}, type: {1}, units: {2})".format(s_register, s_type, s_units))	

			self._Channels.append(self._Channel("SPI", spi_bus, spi_device, stpm3x.error, _sensors))
			self._logger.info("CHANNEL ADDED: SPI[{0}, {1}] STPM3X device with {2} sensors.".format(spi_bus, spi_device, len(_sensors)))

		else:
			self._logger.error("SPI channel setup unknown device type {0}".format(device_type))
			return

				
	def setupChannels(self):
		'''
		Attempt to setup channels for each hardware configuration channel found in CHDIR
		'''
		ch_config_pattern = os.path.join(CHDIR, 'ch*_config.json')
		channel_configs = glob.glob(ch_config_pattern) # e.g., [ ".../ch0_config.json", ".../ch1_config.json", ... ]

		for ch_config in channel_configs:
			# read config into object
			with open(ch_config, 'r') as f:
				config = json.load(f)

			# configure channel based on bus type
			bus_type = config['_bus_type']

			if bus_type == 'SPI':
				self.setupSpiChannel(config['_spi_config'], config['sensors'])
			else:
				self._logger.error("Unknown channel bus type {0}".format(bus_type))


	def updateChannels(self):
		'''
		Runs through each channel's sensors and reads their value into the value property
		'''
		self.syncSensors()
		
		for ch in self._Channels:
			# update sensor values
			if not ch.error:
				for s in ch.sensors:
					s.read()

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

