from drivers import stpm34
from datetime import datetime
import time
import curses


def scaleVI_chs(ivraw):
    vrms = (ivraw['val'] & 0x3fff)
    vrms_scaled = vrms * 0.035211
    irms = ((ivraw['val'] & (0x7fff << 15)) >> 15)
    irms_scaled = irms * 0.00333333
    return {'irms':irms_scaled, 'vrms':vrms_scaled}

def readCME_chs():
    afe0.sync()
    afe1.sync()

    iv1 = afe0.readRow(36)
    iv2 = afe0.readRow(37)

    iv3 = afe1.readRow(36)
    iv4 = afe1.readRow(37)
    
    iv1_scaled = scaleVI_chs(iv1)
    iv2_scaled = scaleVI_chs(iv2)
    iv3_scaled = scaleVI_chs(iv3)
    iv4_scaled = scaleVI_chs(iv4)

    return iv1_scaled,iv2_scaled,iv3_scaled,iv4_scaled

def pbar(window):
    #for i in range(10):
    i = 0;
    while(1):
        data = readCME_chs()
        lineStr = [''] * 24     #terminal default is 24 lines
        lineStr[0] = 'Project Avalanche!'
        lineStr[2] = '    Channel 1    |    Channel 2    |    Channel 3    |    Channel 4'
        lineStr[3] = '-----------------+-----------------+-----------------+-----------------'
        lineStr[4] =  ' Vrms:{:8.3f} V | Vrms:{:8.3f} V | Vrms:{:8.3f} V | Vrms:{:8.3f} V'.format(data[0]['vrms'],data[1]['vrms'],data[2]['vrms'],data[3]['vrms'])
        lineStr[5] =  ' Irms:{:8.3f} A | Irms:{:8.3f} A | Irms:{:8.3f} A | Irms:{:8.3f} A'.format(data[0]['irms'],data[1]['irms'],data[2]['irms'],data[3]['irms'])

        lineStr[21] = 'Last Update: ' + datetime.strftime(datetime.now(),'%B %d, %Y  %I:%M:%S %p')
        lineStr[23] = 'Use Ctrl-C to exit'

        for line,string in enumerate(lineStr):
            window.addstr(line,0,string)

        window.refresh()
        time.sleep(1)


#setup afe board 1            
afe0 = stpm34(0,0)
afe0.hardwareReset()
afe0.writeRowUpper(12,0x0327)   #set ch1 current gain to x2
afe0.readConfigRegs()

#setup afe board 1            
afe1 = stpm34(0,1)
afe1.hardwareReset()
afe1.writeRowUpper(12,0x0327)   #set ch1 current gain to x2
afe1.readConfigRegs()

#start display/update loop
curses.wrapper(pbar)
