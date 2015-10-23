from drivers import stpm34
from datetime import datetime
import time
import curses


afe0 = stpm34(0,0)
afe0.hardwareReset()
afe0.writeRowUpper(12,0x0327)   #set ch1 current gain to x2
afe0.readConfigRegs()

print ''
print 'Starting...'
print ''


while(1):
    afe0.sync()
    a = afe0.readRow(36)
    #b = afe0.readRow(24)

    #v1 = b['val'] & 0x0FFF
    v1rms = (a['val'] & 0x3fff)
    v1rms_scaled = v1rms * 0.035211
    c1rms = ((a['val'] & (0x7fff << 15)) >> 15)
    c1rms_scaled = c1rms * 0.003333333
    
    print datetime.now()
    print '--------------------'
    print 'Voltage 1: {:8f} ({:d})'.format(v1rms_scaled,v1rms) 
    print 'Current 1: {:8f} ({:d})'.format(c1rms_scaled,c1rms) 
    #print v1

    time.sleep(3)
    

#end while
