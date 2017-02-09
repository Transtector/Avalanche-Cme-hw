# Common logging module
import logging, logging.handlers

from .common import Config

# configure app logging default logs to screen only if DEBUG set in config
Logger = logging.getLogger(__name__)

# logger shouldn't filter any log levels - leave that up to the handlers
Logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s %(levelname)-8s [%(name)s] %(message)s',
							   datefmt='%Y-%m-%d %H:%M:%S')

# always send app log to file
fh = logging.handlers.RotatingFileHandler(Config.HWLOG,
										  maxBytes=Config.LOGBYTES,
										  backupCount=Config.LOGCOUNT)
# increase level if DEBUG set
if Config.DEBUG:
	fh.setLevel(logging.DEBUG)
else:
	fh.setLevel(logging.INFO)

# use same formatting for file
fh.setFormatter(formatter)
Logger.addHandler(fh)

# Log to console too if DEBUG set
if Config.DEBUG:
	h = logging.StreamHandler()
	h.setFormatter(logging.Formatter('%(message)s'))
	Logger.addHandler(h)
