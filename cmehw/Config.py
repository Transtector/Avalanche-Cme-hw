# Cme-hw configuration
import os

DEBUG = True

APPROOT = os.path.abspath(os.getcwd()) # /root/Cme-hw/

# logging to files in parent foldr
USERDATA = os.path.abspath('/data') # Cme user data is stored here

# Note - if USERDATA set properly, this will match the same location
# that the Cme uses for logging.
LOGDIR = os.path.abspath(os.path.join(USERDATA, 'log')) # /data/log 
APPLOG = os.path.join(LOGDIR, 'cme-hw.log')
LOGBYTES = 1024 * 50
LOGCOUNT = 1

# channel data and configuration are stored here
CHDIR = os.path.abspath(os.path.join(USERDATA, 'channels')) # /data/channels

# Create folders if not already there
for p in [ LOGDIR, CHDIR ]:
	if not os.path.exists(p):
		os.makedirs(p)


# RRD (Round-Robin Database) Cache Daemon (RRDCACHED)
# This runs on port 42217 by default and there must either be an
# rrdcached running on the localhost _OR_ you can start the cme-mc
# docker with port 42217 mapped to the host machine by running it.
# See the comments at the top of cme-mc/alpine-rrdcached.docker.
# JJB: Current set to None to prevent its use - it ain't working so well.
RRDCACHED = None # "localhost"


# Main hardware polling loop speed
LOOP_PERIOD_s = 1.0
