

import crcmod.predefined
import struct

DSPCR1_REGADDR  = 0x00
DSPCR2_REGADDR  = 0x02
DSPCR3_REGADDR  = 0x04
DSPCR4_REGADDR  = 0x06
DSPCR5_REGADDR  = 0x08
DSPCR6_REGADDR  = 0x0A
DSPCR7_REGADDR  = 0x0C
DSPCR8_REGADDR  = 0x0E
DSPCR9_REGADDR  = 0x10
DSPCR10_REGADDR = 0x12
DSPCR11_REGADDR = 0x14
DSPCR12_REGADDR = 0x16

DFECR1_REGADDR  = 0x18
DFECR2_REGADDR  = 0x1A

DSPIRQ1_REGADDR = 0x1C
DSPIRQ2_REGADDR = 0x1E

DSPSR1_REGADDR  = 0x20
DSPSR2_REGADDR  = 0x22

USREG1_REGADDR  = 0x24
USREG2_REGADDR  = 0x26
USREG3_REGADDR  = 0x28

DSPEV1_REGADDR  = 0x2A
DSPEV2_REGADDR  = 0x2C

DSPREG1_REGADDR = 0x2E
DSPREG2_REGADDR = 0x30
DSPREG3_REGADDR = 0x32
DSPREG4_REGADDR = 0x34
DSPREG5_REGADDR = 0x36
DSPREG6_REGADDR = 0x38
DSPREG7_REGADDR = 0x3A
DSPREG8_REGADDR = 0x3C
DSPREG9_REGADDR = 0x3E
DSPREG10_REGADDR = 0x40
DSPREG11_REGADDR = 0x42
DSPREG12_REGADDR = 0x44
DSPREG13_REGADDR = 0x46
DSPREG14_REGADDR = 0x48
DSPREG15_REGADDR = 0x4A
DSPREG16_REGADDR = 0x4C
DSPREG17_REGADDR = 0x4E
DSPREG18_REGADDR = 0x50
DSPREG19_REGADDR = 0x52

PH1REG1_REGADDR  = 0x54
PH1REG2_REGADDR  = 0x56
PH1REG3_REGADDR  = 0x58
PH1REG4_REGADDR  = 0x5A
PH1REG5_REGADDR  = 0x5C
PH1REG6_REGADDR  = 0x5E
PH1REG7_REGADDR  = 0x60
PH1REG8_REGADDR  = 0x62
PH1REG9_REGADDR  = 0x64
PH1REG10_REGADDR = 0x66
PH1REG11_REGADDR = 0x68
PH1REG12_REGADDR = 0x6A

PH2REG1_REGADDR  = 0x6C
PH2REG2_REGADDR  = 0x6E
PH2REG3_REGADDR  = 0x70
PH2REG4_REGADDR  = 0x72
PH2REG5_REGADDR  = 0x74
PH2REG6_REGADDR  = 0x76
PH2REG7_REGADDR  = 0x78
PH2REG8_REGADDR  = 0x7A
PH2REG9_REGADDR  = 0x7C
PH2REG10_REGADDR = 0x7E
PH2REG11_REGADDR = 0x80
PH2REG12_REGADDR = 0x82

TOTREG1_REGADDR = 0x84
TOTREG2_REGADDR = 0x86
TOTREG3_REGADDR = 0x88
TOTREG4_REGADDR = 0x8A


def calcMask(width, position):
	return ((2 ** width) - 1) << position


class STPM3X:
	#RMS Voltages
	V1RMS = {'address': DSPREG14_REGADDR, 'width': 15, 'position': 0, 'mask': calcMask(15,0)}
	V2RMS = {'address': DSPREG15_REGADDR, 'width': 15, 'position': 0, 'mask': calcMask(15,0)}

	#RMS Currents
	C1RMS = {'address': DSPREG14_REGADDR, 'width': 17, 'position': 15, 'mask': calcMask(17,15)}
	C2RMS = {'address': DSPREG15_REGADDR, 'width': 17, 'position': 15, 'mask': calcMask(17,15)}

	#Apparent Energy Mode
	AEM1 = {'address': DSPCR1_REGADDR, 'width': 1, 'position': 17, 'mask': calcMask(1,17)}
	AEM2 = {'address': DSPCR2_REGADDR, 'width': 1, 'position': 17, 'mask': calcMask(1,17)}
	AEM_APPARENT_RMS_POWER = 0b0
	AEM_APPARENT_VECTORIAL_POWER = 0b1

	#Apparent Vectorial Power Mode
	APM1 = {'address': DSPCR1_REGADDR, 'width': 1, 'position': 18, 'mask': calcMask(1,18)}
	APM2 = {'address': DSPCR2_REGADDR, 'width': 1, 'position': 18, 'mask': calcMask(1,18)}
	APM_FUNDAMENTAL_POWER = 0b0
	APM_ACTIVE_POWER = 0b1

	#Digital Front End Control Registers
	GAIN1 = {'address': DFECR1_REGADDR, 'width': 2, 'position': 26, 'mask': calcMask(2,26)}
	GAIN2 = {'address': DFECR2_REGADDR, 'width': 2, 'position': 26, 'mask': calcMask(2,26)}
	GAIN_X2  = 0b00
	GAIN_X4  = 0b01
	GAIN_X8  = 0b10
	GAIN_X16 = 0b11

	#Temperature Compensation Parameters
	TC1 = {'address': DFECR1_REGADDR, 'width': 3, 'position': 6, 'mask': calcMask(3,6)}
	TC2 = {'address': DFECR2_REGADDR, 'width': 3, 'position': 6, 'mask': calcMask(3,6)}
	TEMP_COEF_NEG50  = 0b000
	TEMP_COEF_NEG25  = 0b001
	TEMP_COEF_ZERO   = 0b010
	TEMP_COEF_POS25  = 0b011
	TEMP_COEF_POS50  = 0b100
	TEMP_COEF_POS75  = 0b101
	TEMP_COEF_POS100 = 0b110
	TEMP_COEF_POS125 = 0b111

	#Reference Frequency
	REF_FREQ = {'address': DSPCR3_REGADDR, 'width': 1, 'position': 27, 'mask': calcMask(1,27)}
	REF_FREQ_50HZ = 0b0
	REF_FREQ_60HZ = 0b1
	

# STPM3X sensor configuration
# Override defaults by passing them at construction, e.g.:
#   s = Config() # provides default configuration
#   s = Config({ 'spi_device': 1 }) # overrides default 'spi_device' value
class Config(dict):

	def __init__(self, *args, **kwargs):
		self['type'] = 'STPM34'
		self['gpio_sync'] = 12
	
		# SPI Interface
		self['spi_bus'] = 0
		self['spi_device'] = 0
		
		# ZCR/CLK Pin
		self['ZCR_SEL'] = 0
		self['ZCR_EN'] = 0
		
		# Tamper
		self['TMP_TOL'] = 0
		self ['TMP_EN'] = 0
		
		# LED1 Settings
		self['LED1OFF'] = True
		self['LPW1'] = 0
		self['LPS1'] = 0
		self['LCS1'] = 0
		
		# LED2 Settings
		self['LED2OFF'] = True
		self['LPW2'] = 0
		self['LPS2'] = 0
		self['LCS2'] = 0

		# System Settings
		self['EN_CUM'] = False
		self['REF_FREQ'] = STPM3X.REF_FREQ_60HZ
		
		# Primary Channel Settings
		self['GAIN1'] = STPM3X.GAIN_X2
		self['CLRSS1'] = False
		self['ENVREF1'] = True
		self['TC1'] = STPM3X.TEMP_COEF_ZERO
		self['AEM1'] = STPM3X.AEM_APPARENT_RMS_POWER
		self['APM1'] = STPM3X.APM_FUNDAMENTAL_POWER
		self['BHPFV1'] = True
		self['BHPFC1'] = True
		self['ROC1'] = False
		self['voltage_swell_threshold'] = 1023
		self['voltage_sag_threshold'] = 0
		self['current_swell_threshold'] = 1023
		self['rms_upper_threshold'] = 4095
		self['rms_lower_threshold'] = 4095
		
		# Secondary Channel Settings 
		self['GAIN2'] = STPM3X.GAIN_X2
		self['CLRSS2'] = False
		self['ENVREF2'] = True
		self['TC2'] = STPM3X.TEMP_COEF_ZERO
		self['AEM2'] = STPM3X.AEM_APPARENT_RMS_POWER
		self['APM2'] = STPM3X.APM_FUNDAMENTAL_POWER
		self['BHPFV2'] = True
		self['BHPFC2'] = True
		self['ROC2'] = False
		self['voltage_swell_threshold'] = 1023
		self['voltage_sag_threshold'] = 0
		self['current_swell_threshold'] = 1023
		self['rms_upper_threshold'] = 4095
		self['rms_lower_threshold'] = 4095

		# set passed items
		for k, v in dict(*args, **kwargs).items():
			self[k] = v


class Stpm3x(object):

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
					self.error += ', ' + error_msg
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
