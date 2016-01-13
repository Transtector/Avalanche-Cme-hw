import os, errno
import stpm3x

APPROOT = os.path.abspath(os.getcwd()) # /home/pi/Cme-hw
LOGDIR = os.path.join(APPROOT, 'log') # /home/pi/Cme-hw/log TODO: look into external/removable location


LOG_MAX_SIZE = 10 # channels log a record to their log file every time through hw loop

LOOP_PERIOD_s = 1.0 # hw loop repeats this number of seconds


# create the log directory if necessary
if not os.path.exists(LOGDIR):
	os.makedirs(LOGDIR)

# spi bus sensor configurations
SPI_SENSORS = [ 

	stpm3x.Config(),

	stpm3x.Config({
		'spi_device': 1
	})
]
