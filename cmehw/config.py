# Hardware Loop (hwloop.py) configuration

import os
import STPM3X

DEBUG = True

APPROOT = os.path.abspath(os.getcwd()) # /root/Cme-hw/

# logging to files in parent foldr
USERDATA = os.path.abspath('/data') # Cme user data is stored here

# Note - if USERDATA set properly, this will match the same location
# that the Cme uses for logging.
LOGDIR = os.path.abspath(os.path.join(USERDATA, 'log')) # /data/log 
APPLOG = os.path.join(LOGDIR, 'cme-hw.log')
LOGBYTES = 1024 * 10
LOGCOUNT = 5

# create the log directory if necessary
if not os.path.exists(LOGDIR):
	os.makedirs(LOGDIR)

# Memcache server is generally the same machine (localhost or 127.0.0.1)
# but if you comment out the appropriate line in /etc/memcached.conf,
# then external machines (e.g., Cme running on another machine) can
# connect and use the Cme-hw running here.
MEMCACHE = 'cme-memcached:11211'


# Channels keep arrays of their sensor and control data every time
# the channel data is published.  Entries in the channel sensor log
# files follow this pattern:
#
# [ <timestamp>, <sensor_0_value>, ..., <sensor_N_value> ]
#
# New entries are appended lines in the file, so the newest recorded
# point is at the end of the file.  These files can grow up to a
# maximum number of entries before dropping the earliest point each
# time a new point is appended.
#
# Each entry in the log file can be a length (for a channel with N sensors):
#
# 	brackets				 2
# 	timestamp				17
# 	comma-space				 2
# 	N sensor values			13 * N
# 	N-1 comma-space			 2 * (N-1)
# 	-------------------------=-----------
# 	Total            21 + N*13 + (N-1)*2 (= 49 for 2 sensors)
#
# So, for our baseline 2 sensors per channel we're logging 49 bytes
# per hardware loop.  The memcache server has an entry size limit as
# well (default is 1MB, but we increase it to 10MB) over which the
# entire log file should be able to be transferred.

LOG_MAX_SIZE = 200000 # gives log file sizes somewhere under 10 MB 

# Sensor read/publish/log loop repeats this number of seconds.
# Change this in conjunction with the LOG_MAX_SIZE above, as
# every time through loop logs a record (line) for every (non-errored)
# channel on the Cme.

LOOP_PERIOD_s = 1.0

# Data log history length is approximately 
# ( LOG_MAX_SIZE * LOOP_PERIOD_s ) / ( 3600 * 24) days

# spi bus sensor configurations
SPI_SENSORS = [

	STPM3X.Config({
		'spi_device': 0,
		'CHV1': 0x85C,
		'CHV2': 0x7FF,
		'CHC1': 0x800,
		'CHC2': 0x800,
	}),

	STPM3X.Config({
		'spi_device': 1,
		'CHV1': 0x7ED,
		'CHV2': 0x7E7,
		'CHC1': 0x800,
		'CHC2': 0x800,
	})
]
