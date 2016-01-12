import crcmod.predefined
import RPi.GPIO as GPIO
import spidev
import struct
import time
from stpm3x import STPM3X

#GPIO assignments
AVALANCHE_GPIO_SENSOR_POWER     = 5
AVALANCHE_GPIO_ISOLATE_SPI_BUS  = 6

AVALANCHE_GPIO_SYNC_SENSOR0     = 12
AVALANCHE_GPIO_SYNC_SENSOR1     = 13

AVALANCHE_GPIO_RELAY_CHANNEL1   = 28
AVALANCHE_GPIO_RELAY_CHANNEL2   = 29
AVALANCHE_GPIO_RELAY_CHANNEL3   = 30
AVALANCHE_GPIO_RELAY_CHANNEL4   = 31

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
			device = stpm3x(spi, spi_config)

			# add two channels for each stmp3x SPI device
			for channel_index in [0, 1]:

				# each SPI device channel has 2 sensors
				sensors = []

				# SPI read and gated read parameters depend on the channel index
				v_read_param = STPM3X.V2RMS if (channel_index == 0) else STPM3X.V1RMS
				c_read_param = STPM3X.C2RMS if (channel_index == 0) else STPM3X.C1RMS

				# TODO: Read scale factors from config
				def v_read():
					volts = device.read(v_read_param) * 0.035430 
					print "        %s Ch[%d].VOLTS = %f" % (spi, channel_index, volts)
					return volts

				def c_read():
					amps = device.gatedRead(c_read_param, 7) * 0.003333
					print "        %s Ch[%d].AMPS = %f" % (spi, channel_index, amps)
					return amps

				print "    Ch[%d] adding 2 sensors:" % (channel_index)

				sensors.append(self._Sensor('AC_VOLTAGE', 'Vrms', 0, v_read))
				sensors.append(self._Sensor('AC_CURRENT', 'Arms', 0, c_read))

				for j, s in enumerate(sensors):
					s.value = s.read()
					print "        Ch[%d]:S[%d].value = %f %s" % (channel_index, j, s.value, s.unit)
					

				# save SPI device channels, their error state, and array of sensors
				self._Channels.append(self._Channel(device, device.error, sensors))


	def readSpiChannels(self):
		'''
		Runs through each channel's sensors and reads updated values
		'''
		for i, ch in enumerate(self._Channels):
			# update sensor values
			for j, s in enumerate(ch.sensors):
				s.value = s.read()
				print "    %s Ch[%d]:S[%d].value = %f %s" % (str(ch.device._spiHandle), i, j, s.value, s.unit)

		return self._Channels

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
		time.sleep(.001)
		GPIO.output(AVALANCHE_GPIO_SYNC_SENSOR0, GPIO.HIGH)
		GPIO.output(AVALANCHE_GPIO_SYNC_SENSOR1, GPIO.HIGH)

		return time.time()


class stpm3x(object):

	_spiHandle = 0;
	
	def __init__(self, spiHandle, config):
		self._spiHandle = spiHandle
		self.error = '' # empty for no errors

		print '\nConfiguring channels on %s ...' % str(spiHandle)

		status = 0
		for i, g in enumerate(['GAIN1', 'GAIN2']):
			if not g in config:
				error_msg = 'SPI channel %d error: missing %s configuration' % (i, g)
				self.error = '    ' + error_msg
				print error_msg

			else:
				gain_param = STPM3X.GAIN1 if (i == 0) else STPM3X.GAIN2

				status |= self.write(gain_param, config[g])

				if not status == 0:
					error_msg = 'SPI channel %d error: error writing %s to device' % (i, g)
					self.error = error_msg
					print '    ' + error_msg
				else:
					print '    done'
	
	def test(self):
		print 'hello world'

	def _bytes2int32_rev(self,data_bytes):
		result = 0
		result += data_bytes[0]
		result += data_bytes[1] << 8
		result += data_bytes[2] << 16
		result += data_bytes[3] << 24             
		return result

	def _bytes2int32(self,data_bytes):
		result = 0
		result += data_bytes[3]
		result += data_bytes[2] << 8
		result += data_bytes[1] << 16
		result += data_bytes[0] << 24             
		return result

	def _crc8_calc(self,data):
		crc8_func = crcmod.predefined.mkCrcFun('crc-8')
		hex_bytestring = struct.pack('>I',data)
		crc = crc8_func(hex_bytestring)
		return crc

	def _readRegister(self, addr):
		self._spiHandle.xfer2([addr, 0xFF, 0xFF, 0xFF, 0xFF])
		readbytes = self._spiHandle.readbytes(5)
		val = self._bytes2int32_rev(readbytes[0:4])
		return val

	def _writeRegister(self, address, data):
		upperMSB = (data >> 24) & 0xFF
		#print '0x{:02x}'.format(upperMSB)
		upperLSB = (data >> 16) & 0xFF
		#print '0x{:02x}'.format(upperLSB)
		lowerMSB = (data >> 8) & 0xFF
		#print '0x{:02x}'.format(lowerMSB)
		lowerLSB = data & 0xFF
		#print '0x{:02x}'.format(lowerLSB)
		
		#Generate packet for lower portion of register
		packet = self._bytes2int32([0x00, address, lowerLSB, lowerMSB])
		crc = self._crc8_calc(packet)
		self._spiHandle.xfer2([0x00, address, lowerLSB, lowerMSB, crc])

		#Generate packet for uper portion of register
		packet = self._bytes2int32([0x00, address+1, upperLSB, upperMSB])
		#print '0x{:08x}'.format(packet)
		crc = self._crc8_calc(packet)
		#print '0x{:02x}'.format(crc) 
		self._spiHandle.xfer2([0x00, address+1, upperLSB, upperMSB, crc])

		#Read back register
		readbytes = self._spiHandle.readbytes(5)
		val = self._bytes2int32_rev(readbytes[0:4])
		crc = readbytes[4]
		return {'val':val, 'crc':crc}

	def printRegister(self, value):
		print '0x{:08x}'.format(value)

	def readConfigRegs(self):
		#read configuration registers
		print 'Configuration Registers'
		for row in xrange(0,21,1):
			addr = row*2
			regvalue = self.readReg(addr)       
			print '{:02d} 0x{:02x} 0x{:08x}'.format(row, addr, regvalue)
		#end for

	def softwareReset(self):
		rd_addr = 0x04
		wr_addr = 0x05
		data = 0xFFFF
		regvalue = self.writeReg(rd_addr, wr_addr, data)

	def _modify(self, register, value):
		mask = register['mask']
		nMask = ~mask
		position = register['position']
		shift = value << position
		
		#read current value
		currentValue = self._readRegister(register['address'])
		#self.printRegister(currentValue)

		#modify value
		newValue = (currentValue & nMask) | ((value << position) & mask)

		return newValue
  
	def convert(self, value, bits):
		'''
		Convert function based on code found here:
		stackoverflow.com/questions/3222088/simulating-cs-sbyte-8-bit-signed-integer-casting-in-python
		'''
		x = (2 ** bits) - 1
		y = (2 ** bits) / 2
		return ((x & value ^ y) - y)

	def read(self, register):

		regValue = self._readRegister(register['address'])
		#print("Register Value: " + hex(regValue))
									  
		#get value from register, mask and shift
		maskedValue = (regValue & register['mask']) >> register['position']
		#print("Masked Value:   " + hex(maskedValue))

		#convert signed value of various bit width to signed int
		value = self.convert(maskedValue, register['width'])
		#print ("Converted Value: " + str(value))
		
		return value

	def gatedRead(self, register, gateThreshold):

		regValue = self._readRegister(register['address'])
		#print("Register Value: " + hex(regValue))
									  
		#get value from register, mask and shift
		maskedValue = (regValue & register['mask']) >> register['position']
		#print("Masked Value:   " + hex(maskedValue))

		#convert signed value of various bit width to signed int
		value = self.convert(maskedValue, register['width'])
		#print ("Converted Value: " + str(value))
		
		if (value < gateThreshold):
			gatedValue = 0
		else:
			gatedValue = value

		return gatedValue

	def write(self, register, value):
		#read and modify register contents
		newValue = self._modify(register, value)
		#self.printRegister(newValue)

		#write to device
		self._writeRegister(register['address'], newValue)

		#read value from device and check if write was successful
		currentValue = self._readRegister(register['address'])
		#self.printRegister(currentValue)

		if (currentValue == newValue):
			return 0
		else:
			return -1
