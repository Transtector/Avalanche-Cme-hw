
import sys
import logging, logging.handlers
import config
import memcache
from Avalanche import Avalanche

# configure app logging default logs to screen only if DEBUG set in config
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s [%(name)s] %(message)s',
							   datefmt='%Y-%m-%d %H:%M:%S')

# always send app log to file
fh = logging.handlers.RotatingFileHandler(config.APPLOG,
										  maxBytes=config.LOGBYTES,
										  backupCount=config.LOGCOUNT)
# increase level if DEBUG set
if config.DEBUG:
	fh.setLevel(logging.DEBUG)
else:
	fh.setLevel(logging.INFO)

# use same formatting for file
fh.setFormatter(formatter)
logger.addHandler(fh)

# Log to console too if DEBUG set
if config.DEBUG:
	h = logging.StreamHandler()
	h.setFormatter(logging.Formatter('%(message)s'))
	logger.addHandler(h)


logger.info("Avalanche ({0}) is rumbling...".format(__name__))

# create shared memory object - terminate on failure
mc = memcache.Client([config.MEMCACHE], debug=0)

TEST_CONNECT = 'this_is_a_test'
mc.set('TEST', TEST_CONNECT)
if not mc.get('TEST') == TEST_CONNECT:
	logger.error("Memcache connection failure ({0})".format(config.MEMCACHE))
	sys.exit(1)

mc.delete('TEST')
logger.info("Memcache {0} connected".format(config.MEMCACHE))


# initialize the Avalanche main board and sensor buses
avalanche = Avalanche(config)

