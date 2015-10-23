import crcmod.predefined
import RPi.GPIO as GPIO
import spidev
import struct
import time


class stpm34(object):

    _spi = 0
    _bus = 0;
    _device = 0
    
    def __init__(self, bus, device):
        #setup SPI
        self._bus = bus
        self._device = device 
        self._spi = spidev.SpiDev()
        self._spi.open(self._bus, self._device)
        #spi.max_speed_hz = 50000
        self._spi.mode = 3     # (CPOL = 1 | CPHA = 1) (0b11)

        #setup GPIO
        GPIO.setmode(GPIO.BCM)
        if self._device == 0:
            GPIO.setup(12, GPIO.OUT, initial=GPIO.HIGH)
        else:
            GPIO.setup(13, GPIO.OUT, initial=GPIO.HIGH)
        

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

    def sync(self):
        if self._device == 0:
            GPIO.output(12, GPIO.LOW)
            time.sleep(.001)
            GPIO.output(12, GPIO.HIGH)
        else:
            GPIO.output(13, GPIO.LOW)
            time.sleep(.001)
            GPIO.output(13, GPIO.HIGH)

    def hardwareReset(self):
        self.sync()
        time.sleep(.001)
        self.sync()
        time.sleep(.001)
        self.sync()
        time.sleep(.001)

    def readReg(self, addr):
        self._spi.xfer2([addr, 0xFF, 0xFF, 0xFF, 0xFF])
        readbytes = self._spi.readbytes(5)
        val = self._bytes2int32_rev(readbytes[0:4])
        crc = readbytes[4]
        return {'val':val, 'crc':crc}

    def readRow(self, row):
        addr = row*2
        self._spi.xfer2([addr, 0xFF, 0xFF, 0xFF, 0xFF])
        readbytes = self._spi.readbytes(5)
        val = self._bytes2int32_rev(readbytes[0:4])
        crc = readbytes[4]
        return {'val':val, 'crc':crc}

    def writeReg(self,rd_addr, wr_addr, data):
        msb = (data >> 8) & 0xFF
        lsb = data & 0xFF
        #Generate packet for lower portion of register
        packet = self._bytes2int32([rd_addr, wr_addr, lsb, msb])
        crc = self._crc8_calc(packet)
        #print '0x{:02X} 0x{:02X} 0x{:08X}  0x{:02X}'.format(rd_addr, wr_addr, packet, crc)
        self._spi.xfer2([rd_addr, wr_addr, lsb, msb, crc])

        #Read back register
        readbytes = self._spi.readbytes(5)
        val = self._bytes2int32_rev(readbytes[0:4])
        crc = readbytes[4]
        return {'val':val, 'crc':crc}

    def writeRowUpper(self,row,data):
        addr = row * 2
        self.writeReg(addr,addr+1,data)

    def writeRowLower(self,row,data):
        addr = row * 2
        self.writeReg(addr,addr,data)
        

    def readConfigRegs(self):
        #read configuration registers
        print 'Configuration Registers'
        for row in xrange(0,21,1):
            addr = row*2
            regvalue = self.readReg(addr)       
            print '{:02d} 0x{:02x} 0x{:08x} 0x{:02x}'.format(row, addr, regvalue['val'], regvalue['crc'])
        #end for

    def softwareReset(self):
        rd_addr = 0x04
        wr_addr = 0x05
        data = 0xFFFF
        regvalue = self.writeReg(rd_addr, wr_addr, data)

