import os, logging, time, glob, json

from collections import deque


import RPi.GPIO as GPIO
import spidev

from .common import Config

# load the STPM3X module and import Stpm3x class
from .STPM3X import Stpm3x
from .Alarms import Alarm

# GPIO assignments
#AVALANCHE_GPIO_SENSOR_POWER     = 5
#AVALANCHE_GPIO_ISOLATE_SPI_BUS  = 6

AVALANCHE_GPIO_SYNC_SENSOR0     = 12

#AVALANCHE_GPIO_RELAY_CHANNEL1   = 28
#AVALANCHE_GPIO_RELAY_CHANNEL2   = 29
#AVALANCHE_GPIO_RELAY_CHANNEL3   = 30
#AVALANCHE_GPIO_RELAY_CHANNEL4   = 31

#AVALANCHE_GPIO_LED1 = 32
#AVALANCHE_GPIO_LED2 = 33
#AVALANCHE_GPIO_LED3 = 34
#AVALANCHE_GPIO_LED4 = 35
#AVALANCHE_GPIO_LED5 = 36



#AVALANCHE_GPIO_SPI_CE0		    = 8
#AVALANCHE_GPIO_SPI_CE1		    = 7

#AVALANCHE_GPIO_MUX_S0   		= 13
#AVALANCHE_GPIO_MUX_S1   		= 14

AVALANCHE_GPIO_SENSOR_NRST		= 20
AVALANCHE_GPIO_SENSOR_BOOT0		= 21

AVALANCHE_GPIO_ALARM            = 13
AVALANCHE_GPIO_DATA_RDY 		= 25

#AVALANCHE_GPIO_U7_MISO_EN		= 26

#AVALANCHE_GPIO_MUX_PUPD_CNTL    = 19

# Discharge sensors for this long before enabling SPI bus
SPI_BUS_DISCHARGE_WAIT_s = 10

# Hardware channels configurations stored here
CHDIR = Config.PATHS.CHDIR

BUFFER_POINTS = Config.HARDWARE.BUFFER_POINTS

# configure SPI bus
#spi = spidev.SpiDev()
#spi.open(0, 0)
#spi.mode = 3 # (CPOL = 1 | CPHA = 1) (0b11)
#spi.max_speed_hz = 5000000


class _Sensor:
	def __init__(self, id, sensor_type, unit, sensor_range, read_function):
		self.id = id
		self.type = sensor_type
		self.unit = unit
		self.range = sensor_range
		self._read = read_function

		# keep a buffer of values
		# new values are pushed at left (values[0])
		# and oldest value falls off right
		self.values = deque([None for x in range(BUFFER_POINTS)]) 

	def read(self, tick):

		value = self._read() # read the sensor value
		self.values.appendleft([ tick, value ]) # push onto buffer
		self.values.pop() # remove oldest
		return value

	def __repr__(self):
		s = "Sensor {0} type: {1}, unit: {2}, range: {3}".format(self.id, self.type, self.unit, self.range)
		return s


class _Channel:
	def __init__(self, id, bus_type, bus_index, bus_device_index, rra, error, sensors):
		self.id = id
		self.bus_type = bus_type
		self.bus_index = bus_index
		self.bus_device_index = bus_device_index
		self.rra = rra
		self.stale = False
		self.error = error
		self.sensors = sensors

	def __repr__(self):
		s = "Channel {0} has {1} sensors".format(self.id, len(self.sensors))
		for k, v in self.sensors.items():
			s += "\n\t{0}".format(repr(v))
		return s



class _VirtualChannel:
	def __init__(self, id, rra, error, sensors):
		self.id = id
		self.rra = rra
		self.stale = False
		self.error = error
		self.sensors = sensors

	def __repr__(self):
		s = "VirtualChannel {0} has {1} sensors".format(self.id, len(self.sensors))
		for k, v in self.sensors.items():
			s += "\n\t{0}".format(repr(v))
		return s



class Avalanche(object):

	Channels = {} # dict of _Channel

	alarmData = []
	alarmManager = []

	b1_voltage_pha = []
	b1_current_pha = [] 
	b1_voltage_phb = []
	b1_current_phb = []
	b1_voltage_phc = []
	b1_current_phc = []
	b1_status_pha = []
	b1_status_phb = []
	b1_ph_imbalance = []
	b2_voltage_pha = []
	b2_current_pha = [] 
	b2_voltage_phb = []
	b2_current_phb = []
	b2_voltage_phc = []
	b2_current_phc = []
	b1_status_phc = []
	b2_ph_imbalance = []

	alarm_state = False
	alarm_start_time = 0
	alarm_stop_time  = 0

	def alarm_end(self, arg1):
		self.alarm_stop_time = time.time() * 1000

	def alarm(self, arg1):
	#self._logger.info("\n\nAlarm Occurred"))
		if GPIO.input(AVALANCHE_GPIO_ALARM) == GPIO.HIGH:
			self.alarm_start_time = time.time() * 1000

			print("\nAlarm Start: ", self.alarm_start_time)

			self.b1_voltage_pha = []
			self.b1_current_pha = [] 
			self.b1_voltage_phb = []
			self.b1_current_phb = []
			self.b1_voltage_phc = []
			self.b1_current_phc = []
			self.b1_status_pha = []
			self.b1_status_phb = []
			self.b1_ph_imbalance = []
			self.b2_voltage_pha = []
			self.b2_current_pha = [] 
			self.b2_voltage_phb = []
			self.b2_current_phb = []
			self.b2_voltage_phc = []
			self.b2_current_phc = []
			self.b2_status_phc = []
			self.b2_ph_imbalance = []

			self.alarm_state = True
		else:
			self.alarm_stop_time = time.time() * 1000

			print("Alarm Stop : ", self.alarm_stop_time * 1000)



	def __init__(self, alarmManager):

		self._logger = logging.getLogger(__name__)

		self.alarmManager = alarmManager

		self._logger.info("Setting up GPIO")

		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)

		#initialize sensor sync pins
		GPIO.setup(AVALANCHE_GPIO_SYNC_SENSOR0, GPIO.OUT, initial=GPIO.HIGH) # TODO: read from config file
		GPIO.setup(AVALANCHE_GPIO_SENSOR_NRST, GPIO.OUT, initial=GPIO.LOW)
		GPIO.setup(AVALANCHE_GPIO_SENSOR_BOOT0, GPIO.OUT, initial=GPIO.LOW)
		GPIO.setup(AVALANCHE_GPIO_ALARM, GPIO.IN)
		GPIO.setup(AVALANCHE_GPIO_DATA_RDY, GPIO.IN)

		GPIO.add_event_detect(AVALANCHE_GPIO_ALARM, GPIO.BOTH, callback=self.alarm, bouncetime=50)

		#initialize chip enables
		#GPIO.setup(AVALANCHE_GPIO_SPI_CE0, GPIO.OUT, initial=GPIO.LOW)
		#GPIO.setup(AVALANCHE_GPIO_SPI_CE1, GPIO.OUT, initial=GPIO.LOW)
		
		#initialize enables/mux control (Optimus)
		#GPIO.setup(AVALANCHE_GPIO_STPM34_ENABLE, GPIO.OUT, initial=GPIO.LOW)

		#GPIO.setup(AVALANCHE_GPIO_MUX_S0, GPIO.OUT, initial=GPIO.LOW)
		#GPIO.setup(AVALANCHE_GPIO_MUX_S1, GPIO.OUT, initial=GPIO.LOW)

		#GPIO.setup(AVALANCHE_GPIO_U3_MISO_EN, GPIO.OUT, initial=GPIO.LOW)
		#GPIO.setup(AVALANCHE_GPIO_U7_MISO_EN, GPIO.OUT, initial=GPIO.LOW)

		#GPIO.setup(AVALANCHE_GPIO_MUX_PUPD_CNTL, GPIO.OUT, initial=GPIO.LOW)

		self.tick = 0 # tracks sync time

		self._logger.info("Enable/Powerup SPI devices")
		self.enableSequence()

		self._logger.info("Setup channels")
		self.setupChannels()

		self.alarm_state = False


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


	def setupSpiChannel(self, ch_id, spi_config, sensors):

		# setup a new SPI channel using a STPM3X device
		bus_index = spi_config['bus_index']
		device_type = spi_config['device_type']
		device_index = spi_config['device_index']

		ch_rra = spi_config['rra']
		
		# configure SPI bus
		spi = spidev.SpiDev()
		spi.open(bus_index, 0)
		spi.mode = 3 # (CPOL = 1 | CPHA = 1) (0b11)
		spi.max_speed_hz = 5000000

		# The STPM3X sensor read function as a closure to
		# capture register, scale, and threshold config
		def stpm3x_read(sensor_id, device, register, scale, threshold):

			def r():
				#self.selectSensor(device)
				v = stpm3x.read(register, threshold) * scale
				#print("\tREAD {0}.{1}: reg {2} (scale: {3}, threshold: {4}) = {5}".format(ch_id, sensor_id, register, scale, threshold, v))
				return v

			return r


		# configure based on device type
		if device_type == 'STPM3X':

			# Create an STPM3X device object on the SPI bus and pass the configuration.
			# See the STPM3X and Config class in the same module for configuration keys that
			# can be set here to override the defaults in the module.
			#self.selectSensor(device_index)
			stpm3x = Stpm3x(spi, spi_config)

			# Construct a list of sensors for which we have configuration objects (passed in on sensors)
			_sensors = {}

			for sId, s in sensors.items():

				s_config = s['_config']

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

				# Add the sensor the the _sensors for the Channel
				_sensors[sId] = _Sensor(sId, s_type, s_units, s_range, stpm3x_read(sId, device_index, s_register, s_scale, s_threshold))
				self._logger.info("\tSTPMX3 device sensor added (register: {0}, type: {1}, units: {2})".format(s_register, s_type, s_units))	

			self.Channels[ch_id] = _Channel(ch_id, "SPI", bus_index, device_index, ch_rra, stpm3x.error, _sensors)
			self._logger.info("CHANNEL ADDED: {0} SPI[{1}, {2}] STPM3X device with {3} sensors.\n\n".format(ch_id, bus_index, device_index, len(_sensors)))

		else:
			self._logger.error("SPI channel setup unknown device type {0}".format(device_type))
			return

				
	def setupVirtualChannel(self, ch_id, virtual_config, sensors):
		'''
		Virtual channel can pull data from other channels and combine according to 
		methods provided in the configuration.
		'''
		self._logger.info("Configuring VIRTUAL channel {0}".format(ch_id))

		ch_rra = virtual_config['rra']

		# defines the function called when sensors are read
		def s_read(channels, sources, stype):

			def r():
				# find and get references to the source sensors
				_sensor_values = []
				for src in sources:
					ref = src.split('.') # [ chId, sId ]
					_ch = channels.get(ref[0])
					if _ch:
						_s = _ch.sensors.get(ref[1])
					if _s and _s.values and len(_s.values) > 1 and _s.values[0] and len(_s.values[0]) > 1:
						val = _s.values[0][1]
						#print("{0}: {1}.{2} sensor value found: {3}".format(stype, _ch.id, _s.id, val))
						_sensor_values.append(val)
				
				if stype == 'PIB':
					# Phase Imbalance
					if not _sensor_values or len(_sensor_values) < 3:
						#print("ERROR: Not enough source sensor values to calculate phase imbalance.")
						return 0

					# Many references for this calculation, but here I'm going
					# to use the maximum difference from average Vrms to calculate
					Vsum = 0
					for _s in _sensor_values:
						Vsum = Vsum + _s
					Vavg = Vsum / len(_sensor_values)  # RMS average of the phases

					if Vavg == 0:
						#print("PIB: Voltage average is zero cannot calculate phase imbalance")
						return 0 # avoid div by zero

					Vmax = 0
					for _s in _sensor_values:
						m = abs(Vavg - _s)
						Vmax = m if m > Vmax else Vmax

					PI = 100 * (Vmax / Vavg) # Phase Imbalance as percentage

					#print("\n\t[ {0:.2f}, {1:.2f}, {2:.2f} ] Vmax: {3:.2f} Vavg: {4:.2f} PI: {5:.2f} %\n".format(_sensor_values[0], _sensor_values[1], _sensor_values[2], Vmax, Vavg, PI))
					return PI

				else:
					self._logger.error("Unknown virtual channel type: {0}".format(stype))
					return 0

			return r

		_sensors = {} # added to Channels as a dict
		for sId, s in sensors.items():

			s_config = s['_config']

			s_type = s_config['type']
			s_units = s_config['units'] # % - but will not be used in DS name
			s_range = s_config['range']

			# Virtual channel sensors can combine the values from other
			# channels (configured from sources) depending on the type
			# set for the sensor.
			s_sources = s_config['sources'] # [ chId.sId, ...]

			# Add the sensor the the _sensors for the Channel
			_sensors[sId] = _Sensor(sId, s_type, s_units, s_range, s_read(self.Channels, s_sources, s_type))
			self._logger.info("\tVIRTUAL sensor added (type: {0}, units: {1})".format(s_type, s_units))	

		self.Channels[ch_id] = _VirtualChannel(ch_id, ch_rra, False, _sensors)
		self._logger.info("CHANNEL ADDED: {0} VIRTUAL with {1} sensors.\n\n".format(ch_id, len(_sensors)))


	def setupChannels(self):
		'''
		Attempt to setup channels for each hardware configuration channel found in CHDIR
		'''
		ch_config_pattern = os.path.join(CHDIR, 'ch*_config.json')
		channel_configs = glob.glob(ch_config_pattern) # e.g., [ ".../ch0_config.json", ".../ch1_config.json", ... ]

		count = 0
		for ch_config in sorted(channel_configs):
			# read channel _config into object
			with open(ch_config, 'r') as f:
				try:
					ch = json.load(f)
				except Exception as e:
					self._logger.error("Error loading {0} configuration file: {1}".format(ch_config, e))
					continue

			# configure channel based on bus type
			id = os.path.basename(ch_config).split('_')[0] # take id from filename
			config = ch['_config']
			sensors = ch['sensors']
			bus_type = config['bus_type']

			self._logger.info("\n\nSetting up {0} channel as {1} from {2}".format(bus_type, id, ch_config))

			if bus_type == 'SPI':
				self.setupSpiChannel(id, config, sensors)
				count = count + 1

			elif bus_type == 'VIRTUAL':
				self.setupVirtualChannel(id, config, sensors)
				count = count + 1

			else:
				self._logger.error("Unknown channel bus type {0}".format(bus_type))

		self._logger.info("Done setting up {0} channels:".format(count))
		for ch in sorted(self.Channels):
			self._logger.info("\t{0}: {1}".format(ch, self.Channels[ch]))

	def getChannelScales(self):
		'''
		'''
		scales = []

		ch_config_pattern = os.path.join(CHDIR, 'ch*_config.json')
		channel_configs = glob.glob(ch_config_pattern) # e.g., [ ".../ch0_config.json", ".../ch1_config.json", ... ]

		count = 0
		for ch_config in sorted(channel_configs):
			# read channel _config into object
			with open(ch_config, 'r') as f:
				try:
					ch = json.load(f)
				except Exception as e:
					self._logger.error("Error loading {0} configuration file: {1}".format(ch_config, e))
					continue

			# configure channel based on bus type
			id = os.path.basename(ch_config).split('_')[0] # take id from filename
			
			config = ch['_config']
			sensors = ch['sensors']
			
			if config['bus_type'] == "SPI":
				for s in sensors.values():
					scales.append(s['_config']['scale'])

		return scales




	def updateChannels(self):
		'''
		Runs through each channel's sensors and reads their value into the value property
		'''

		if self.alarm_state == True:
			if GPIO.input(AVALANCHE_GPIO_ALARM) == GPIO.LOW:
				'''
				Get the system scale factors
				'''
				scales = self.getChannelScales()
				inst_scales = []

				for scale in scales:
					inst_scales.append(scale / 256)


				'''
				Setup Alarm Structure
				'''
				self.alarm_state = False
				
				new_alarm = Alarm()
				new_alarm.step_ms = 0.000512
				new_alarm.start_ms = self.alarm_start_time
				new_alarm.end_ms = self.alarm_stop_time

				print("Reading Alarm Data...", end='')
				

				#configure SPI bus
				spi = spidev.SpiDev()
				spi.open(0, 0)
				spi.mode = 3 # (CPOL = 1 | CPHA = 1) (0b11)
				spi.max_speed_hz = 5000000

				new_alarm = self.readAlarmSource(spi, new_alarm)

				for sample in range(0,390*2):
					#print("\nSend Block Request: %d", sample)
					sampleMSB = (sample >> 8) & 0xFF
					sampleLSB = (sample >> 0) & 0xFF				

					spi.xfer2([0xF0, sampleLSB, sampleMSB, 0xFF, 0xFF])
					self.readAlarmData(spi, inst_scales)

				# for sample in range(0,390):
				# 	self.b1_voltage_pha.append(500)
				# 	self.b1_current_pha.append(500)
				# 	self.b1_voltage_phb.append(500)
				# 	self.b1_current_phb.append(500)
				# 	self.b1_voltage_phc.append(500)
				# 	self.b1_current_phc.append(500)
				# 	self.b1_status_pha.append(500)
				# 	self.b1_status_phb.append(500)
				# 	self.b1_ph_imbalance.append(500)
				# 	self.b2_voltage_pha.append(500)
				# 	self.b2_current_pha.append(500)
				# 	self.b2_voltage_phb.append(500)
				# 	self.b2_current_phb.append(500)
				# 	self.b2_voltage_phc.append(500)
				# 	self.b2_current_phc.append(500)
				# 	self.b2_status_phc.append(500)
				# 	self.b2_ph_imbalance.append(500)

				spi.xfer2([0xF2, 0xFF, 0xFF, 0xFF, 0xFF])

				spi.close()

				# while GPIO.input(AVALANCHE_GPIO_ALARM) == GPIO.HIGH: {}
				#print(new_alarm)
				#spi.close()
				#print("Alarm Ended")
				# new_alarm.end_ms = 0

				new_alarm.data = {
					"ch0": {
						"s0": self.b1_voltage_pha
					},
					"ch1": {
						"s0": self.b1_voltage_phb
					},
					"ch2": {
						"s0": self.b1_voltage_phc
					},
					"ch3": {
						"s0": self.b1_ph_imbalance
					},
					"ch4": {
						"s0": self.b2_voltage_pha,
						"s1": self.b2_current_pha
					},
					"ch5": {
						"s0": self.b2_voltage_phb,
						"s1": self.b2_current_phb
					},
					"ch6": {
						"s0": self.b2_voltage_phc,
						"s1": self.b2_current_phc
					},
					"ch7": {
						"s0": self.b2_ph_imbalance
					}
				}

				# print(new_alarm)
				# print(new_alarm.data)

				# print("B2 Voltage PHA")
				# print(self.b2_voltage_pha)
				# print("")
				self.alarmManager.InsertAlarm(new_alarm)
				print("Finished")
				print(new_alarm)


 
		for ch in self.Channels.values():
			# update sensor values
			if not ch.error:
				for s in ch.sensors.values():
					s.read(self.tick)

		
		self.tick = self.syncSensors()

		return self.Channels


	def readAlarmSource(self, handle, alarm):
		alarm_source = 0
		rxArray = []

		handle.xfer2([0xF3, 0xFF, 0xFF, 0xFF, 0xFF])
		rxArray = handle.xfer2([0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
		alarm_source = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[0:4])

		b0_pha_swell  = bool(alarm_source & (0x1 << 0))		#ch0
		b0_pha_sag    = bool(alarm_source & (0x1 << 1))
		b0_pha_outage = bool(alarm_source & (0x1 << 2))
		b0_phb_swell  = bool(alarm_source & (0x1 << 3))		#ch1
		b0_phb_sag    = bool(alarm_source & (0x1 << 4))
		b0_phb_outage = bool(alarm_source & (0x1 << 5))
		b0_phc_swell  = bool(alarm_source & (0x1 << 6))		#ch2
		b0_phc_sag    = bool(alarm_source & (0x1 << 7))
		b0_phc_outage = bool(alarm_source & (0x1 << 8))
		b0_ph_imb     = bool(alarm_source & (0x1 << 9))

		b1_pha_swell  = bool(alarm_source & (0x1 << 10))	#ch4
		b1_pha_sag    = bool(alarm_source & (0x1 << 11))
		b1_pha_outage = bool(alarm_source & (0x1 << 12))
		b1_phb_swell  = bool(alarm_source & (0x1 << 13))	#ch5
		b1_phb_sag    = bool(alarm_source & (0x1 << 14))
		b1_phb_outage = bool(alarm_source & (0x1 << 15))
		b1_phc_swell  = bool(alarm_source & (0x1 << 16))	#ch6
		b1_phc_sag    = bool(alarm_source & (0x1 << 17))
		b1_phc_outage = bool(alarm_source & (0x1 << 18))
		b1_ph_imb     = bool(alarm_source & (0x1 << 19))

		#Determine alarm type


		if b0_pha_swell | b0_phb_swell | b0_phc_swell | b1_pha_swell | b1_phb_swell | b1_phc_swell:
			alarm.type = 'SWELL'

		if b0_pha_sag | b0_phb_sag | b0_phc_sag | b1_pha_sag | b1_phb_sag | b1_phc_sag:
			alarm.type = 'SAG'

		if b0_ph_imb | b1_ph_imb:
			alarm.type = 'IMBALANCE'

		if b0_pha_outage | b0_phb_outage | b0_phc_outage | b1_pha_outage | b1_phb_outage | b1_phc_outage:
			alarm.type = 'OUTAGE'

		#Determine alarm channel
		if b0_pha_swell | b0_pha_sag | b0_pha_outage:
			alarm.channel = 'ch0'

		if b0_phb_swell | b0_phb_sag | b0_phb_outage:
			alarm.channel = 'ch1'

		if b0_phc_swell | b0_phc_sag | b0_phc_outage:
			alarm.channel = 'ch2'

		if b0_ph_imb:
			alarm.channel = 'ch3'

		if b1_pha_swell | b1_pha_sag | b1_pha_outage:
			alarm.channel = 'ch4'

		if b1_phb_swell | b1_phb_sag | b1_phb_outage:
			alarm.channel = 'ch5'

		if b1_phc_swell | b1_phc_sag | b1_phc_outage:
			alarm.channel = 'ch6'

		if b1_ph_imb:
			alarm.channel = 'ch7'

		#Determine alarm sensor
		alarm.sensor = 's0'

		return alarm


	def readAlarmData(self, handle, scales):
		txArray = []
		rxArray = []

		for i in range(0,112):
			txArray.append(i)

		txArray[0] = 0xF1

		# Wait for data to be ready
		#print("Waiting for Data Ready signal...") 
		while GPIO.input(AVALANCHE_GPIO_DATA_RDY) == GPIO.LOW: {}
		#print("Read...")
		#time.sleep(0.01)
		rxArray = handle.xfer2(txArray)

		crc32  		 = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[0:4])
		ncrc32		 = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[4:8])

		self.b1_voltage_pha.append(Stpm3x.convert_raw(Stpm3x, rxArray[8:12], 'V1DATA', 0) * scales[0])
		self.b1_current_pha.append(Stpm3x.convert_raw(Stpm3x, rxArray[12:16], 'C1DATA', 0) * 0.02037096)
		self.b1_voltage_phb.append(Stpm3x.convert_raw(Stpm3x, rxArray[16:20], 'V1DATA', 0) * scales[1])
		self.b1_current_phb.append(Stpm3x.convert_raw(Stpm3x, rxArray[20:24], 'C1DATA', 0) * 0.02037096)
		#b1_crmsvrms_pha = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[24:28])
		#b1_crmsvrms_phb = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[28:32])
		#b1_status_pha = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[32:36])
		#b1_status_phb = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[36:40])
		self.b1_voltage_phc.append(Stpm3x.convert_raw(Stpm3x, rxArray[40:44], 'V1DATA', 0) * scales[2])
		self.b1_current_phc.append(Stpm3x.convert_raw(Stpm3x, rxArray[44:48], 'C1DATA', 0) * 0.02037096)
		#b1_crmsvrms_phc = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[48:52])
		#b1_status_phc = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[52:56])
		self.b1_ph_imbalance.append(Stpm3x._bytes2int32_rev(Stpm3x, rxArray[56:60]) / 1000)

		self.b2_voltage_pha.append(Stpm3x.convert_raw(Stpm3x, rxArray[60:64], 'V1DATA', 0) * scales[3])
		self.b2_current_pha.append(Stpm3x.convert_raw(Stpm3x, rxArray[64:68], 'C1DATA', 0) * scales[4])
		self.b2_voltage_phb.append(Stpm3x.convert_raw(Stpm3x, rxArray[68:72], 'V1DATA', 0) * scales[5])
		self.b2_current_phb.append(Stpm3x.convert_raw(Stpm3x, rxArray[72:76], 'C1DATA', 0) * scales[6])
		#b2_crmsvrms_pha = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[76:80])
		#b2_crmsvrms_phb = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[80:84])
		#b2_status_pha = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[84:88])
		#b2_status_phb = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[88:92])
		self.b2_voltage_phc.append(Stpm3x.convert_raw(Stpm3x, rxArray[92:96], 'V1DATA', 0) * scales[7])
		self.b2_current_phc.append(Stpm3x.convert_raw(Stpm3x, rxArray[96:100], 'C1DATA', 0) * scales[8])
		#b2_crmsvrms_phc = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[100:104])
		#b2_status_phc = Stpm3x._bytes2int32_rev(Stpm3x, rxArray[104:108])
		self.b2_ph_imbalance.append(Stpm3x._bytes2int32_rev(Stpm3x, rxArray[108:112]) / 1000)

		'''
		#print(rxArray)
		print("CRC32      : %08x" % crc32)
		print("~CRC32     : %08x" % ncrc32)
		print("Voltage PhA: ", voltage_pha)
		print("Current PhA: ", current_pha)
		print("Voltage PhB: ", voltage_phb)
		print("Current PhB: ", current_phb)
		print("Voltage PhC: ", voltage_phc)
		print("Voltage PhC: ", current_phc)
		print("Phase Imb  : ", ph_imbalance)

		input("Press Enter to continue...")'''
		#self.alarmData.append(rxArray)



	def syncSensors(self):
		'''
		STPM3X sensors can be sync'd by briefly pulling the sync line Low for
		each sensor board.
		'''
		GPIO.output(AVALANCHE_GPIO_SYNC_SENSOR0, GPIO.LOW)
		time.sleep(0.001)
		GPIO.output(AVALANCHE_GPIO_SYNC_SENSOR0, GPIO.HIGH)
		time.sleep(0.001)

		return time.time()


	def setSync(self):
		GPIO.output(AVALANCHE_GPIO_SYNC_SENSOR0, GPIO.HIGH)


	def clrSync(self):
		GPIO.output(AVALANCHE_GPIO_SYNC_SENSOR0, GPIO.LOW)


	#def chipEnableControl(self, channel, state):
		'''
		Relays are SPST. If the output is high, the relay will close its normally
		open contact
		'''
	#	if state == True:
	#		CE_State = GPIO.HIGH
	#	else:
	#		CE_State = GPIO.LOW
#
#		if channel == 1:
#			GPIO.output(AVALANCHE_GPIO_SPI_CE0, CE_State)
#		elif channel == 2:
#			GPIO.output(AVALANCHE_GPIO_SPI_CE1, CE_State)

	#def enableSensors(self):
	#	GPIO.output(AVALANCHE_GPIO_STPM34_ENABLE, GPIO.HIGH)

	#def disableSensors(self):
	#	GPIO.output(AVALANCHE_GPIO_STPM34_ENABLE, GPIO.LOW)

	#def setMuxOuputsPullup(self):
	#	GPIO.output(AVALANCHE_GPIO_MUX_PUPD_CNTL, GPIO.HIGH)

	#def setMuxOuputsPulldown(self):
	#	GPIO.output(AVALANCHE_GPIO_MUX_PUPD_CNTL, GPIO.LOW)


	#def selectSensor(self, device):
	#	if device == 1: #SS1
	#		#print("Select Sensor SS1 - BANK 1")
	#		self.selectVoltageBank(1)
	#		GPIO.output(AVALANCHE_GPIO_MUX_S0, GPIO.HIGH)
	#		GPIO.output(AVALANCHE_GPIO_MUX_S1, GPIO.LOW)
	#	elif device == 2: #SS2
	#		#print("Select Sensor SS2 - BANK 1")
	#		self.selectVoltageBank(1)
	#		GPIO.output(AVALANCHE_GPIO_MUX_S0, GPIO.LOW)
	#		GPIO.output(AVALANCHE_GPIO_MUX_S1, GPIO.LOW)		
	#	elif device == 3: #SS3 or SS4
	#		#print("Select Sensor SS3 - BANK 2")
	#		self.selectVoltageBank(2)
	#		GPIO.output(AVALANCHE_GPIO_MUX_S0, GPIO.HIGH)
	#		GPIO.output(AVALANCHE_GPIO_MUX_S1, GPIO.HIGH)
	#	elif device == 4: #SS3 or SS4
	#		#print("Select Sensor SS4 - BANK 2")
	#		self.selectVoltageBank(2)
	#		GPIO.output(AVALANCHE_GPIO_MUX_S0, GPIO.LOW)
	#		GPIO.output(AVALANCHE_GPIO_MUX_S1, GPIO.HIGH)


	#def selectVoltageBank(self, bank):
	#	if bank == 1:
	#		GPIO.output(AVALANCHE_GPIO_U3_MISO_EN, GPIO.HIGH)
	#		GPIO.output(AVALANCHE_GPIO_U7_MISO_EN, GPIO.LOW)
	#	elif bank == 2:
	#		GPIO.output(AVALANCHE_GPIO_U3_MISO_EN, GPIO.LOW)
	#		GPIO.output(AVALANCHE_GPIO_U7_MISO_EN, GPIO.HIGH)
	#	else:
	#		GPIO.output(AVALANCHE_GPIO_U3_MISO_EN, GPIO.LOW)
	#		GPIO.output(AVALANCHE_GPIO_U7_MISO_EN, GPIO.LOW)

	def enableSequence(self):
		GPIO.output(AVALANCHE_GPIO_SENSOR_NRST, GPIO.HIGH)
		GPIO.output(AVALANCHE_GPIO_SENSOR_BOOT0, GPIO.HIGH)
		time.sleep(0.1)
		GPIO.output(AVALANCHE_GPIO_SENSOR_NRST, GPIO.LOW)

		#STPM init sequence  

		#Ensure all SSx lines are low (PUPD_CTRL = LOW) before enabling the chips with the enable signal
		#self.disableSensors()
		#self.setMuxOuputsPulldown()
		#self.chipEnableControl(1, False)
		#time.sleep(0.5);

		#Enable the sensors chips by transitioning 
		#self.enableSensors()
		#time.sleep(0.2);

		#Set Lines to their default state, SSx lines are HIGH, Sync is HIGH, CE0 is high
		#self.setSync()
		#self.setMuxOuputsPullup()
		#self.chipEnableControl(1, True)
		#time.sleep(0.1)

		#Send the Global Software Reset signal (3 1ms LOW pulses followed by a 1ms LOW Pulse on SSx lines)
		#self.syncSensors()
		#self.syncSensors()
		#self.syncSensors()

		#self.chipEnableControl(1, False)
		#self.setMuxOuputsPulldown()
		#time.sleep(0.001);
		#self.chipEnableControl(1, True)
		#self.setMuxOuputsPullup()


