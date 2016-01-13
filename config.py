import os, errno
import stpm3x

APPROOT = os.path.abspath(os.getcwd()) # /home/pi/Cme-hw
LOGDIR = os.path.join(APPROOT, 'log') # /home/pi/Cme-hw/log TODO: look into external/removable location

# Channels keep arrays of their sensor and control data every time
# the channel data is published.  The maximum channel record size
# can be calculated approximately* as:
#
# Channel_Record_Max_Bytes = 41 * Channel_Sensors + 1 
# 
# * This only consideres a sensor data point as [ <timestamp>, <double> ]
# which may not be a valid assumption for future sensors.
# * Also doesn't consider channel controls, which also log their states
LOG_MAX_SIZE = 1024000

# 1024000 channel records gives log file sizes around 80 MB per channel
# 1024000 records at 1 record per second gives just under 12 days of history

# Sensor read/publish/log loop repeats this number of seconds.
# Change this in conjunction with the LOG_MAX_SIZE above, as
# every time through loop logs a record (line) for every (non-errored)
# channel on the Cme.
LOOP_PERIOD_s = 1.0 

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
