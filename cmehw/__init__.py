
import config
import logging, logging.handlers

# configure app logging default logs to screen only if DEBUG set in config
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s [%(name)s] %(message)s',
							   datefmt='%Y-%m-%d %H:%M:%S')

# set format in default Flask logging StreamHandler for console (DEBUG) output
for h in logger.handlers:
	h.setFormatter(formatter)

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
