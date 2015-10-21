from drivers import stpm34
from datetime import datetime
import time

afe0 = stpm34(0,0)
afe0.softwareReset()
#print "AFE0 Conf Regs Before Write:"
#afe0.readConfigRegs()
#afe0.writeReg(0x06,0x06,0xabcd)
#print "AFE0 Conf Regs After Write:"

afe0.writeRowLower(1,0x0000)
afe0.writeRowUpper(1,0x0400)
afe0.readConfigRegs()

#afe1 = stpm34(0,1)
#afe1.softwareReset()
#print "AFE1 Conf Regs Before Write:"
#afe1.readConfigRegs()
#afe1.writeReg(0x06,0x06,0xdcba)
#print "AFE1 Conf Regs After Write:"
#afe1.readConfigRegs()

text = raw_input('Press enter to continue...')
print ''
print 'starting loop...'

while(1):
    readVal = afe0.readRow(29)
    #row4A = afe0.readReg(0x4a)
    print datetime.now()
    print 'V1    0x{:08X}'.format(readVal['val'])
    #print 'row4A    0x{:08X}  0x{:02X}'.format(row4A['val'], row4A['crc'])
    print ''

    time.sleep(0.5)
    

#end while
