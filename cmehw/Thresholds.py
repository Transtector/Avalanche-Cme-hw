# Threshold processing
#
# Works with hardware channels to save alarms if current channel values are not within nominal
# region defined by channel threshold configuration

import os, json, time, tempfile

from random import randint

from .Logging import Logger
from .common import Config
from .common.Switch import switch
from .common.LockedOpen import LockedOpen

# The location where channel data and configuration are stored (typically /data/channels/)
CHDIR = Config.CHDIR

MAX_ALARM_POINTS = Config.MAX_ALARM_POINTS # how many points collected while in alarm condition
ALARM_LEAD_POINTS = Config.ALARM_LEAD_POINTS # how many pre- and post- alarm points are saved

# Cache the channel configuration files so we
# don't have to read from disk every time through.
CONFIGS_CACHE = {}

# Cache alarms in memory and dump to disk only
# every so often.  Can't be too long in between
# updates, though, as the API layer will read
# alarms from disk.
ALARMS_CACHE = {}

def ProcessAlarms(channel):
	# TODO: We should probably bound the size of the alarm files.

	# Explanation:
	#
	# Alarms are processed on a per-channel basis.  Most of the sequence
	# of events below is pretty self explanatory.  Once we get past the
	# error checking and seeing if we have 'recordAlarms' set True in
	# the channel config file, then the real magic happens.
	#
	# The channel's sensors are processed one at a time, and the threshold
	# values for each sensor is loaded from the channel configuration file.
	# At the same time, the channel alarms history is loaded from the
	# channel alarms file.
	#
	# A history is recorded for a sensor's alarm events.  The history is kept
	# for each sensor's defined thresholds.  So if, for example, a sensor has both
	# a "WARNING" and "ALARM" thresholds defined, then there will be a history
	# for each one of these (in the sensor record for that particular channel
	# alarm file).
	#
	# An alarm history is simply a list of points (which are just pairs of 
	# time and value numbers) that were measured around threshold crossings.
	#
	# To build up an alarm history each sensor's current value is compared
	# against the configured thresholds. This results in either "alarm" 
	# (sensor value exceeds threshold) or "no alarm" condition.
	#
	# We record the sensor's point if "alarm" condition exists. BUT we don't want
	# to just record everything.  So, we examine the sensor's alarm history (just for
	# the particular threshold classification).
	#
	# If there're no prior alarms OR if we're starting a new alarm segment (more on 
	# that to follow), then we'll add the current point and all the sensor's
	# buffered points to the alarms record.  This opens the alarm record.
	#
	# If there are prior alarms AND we're just tacking on another point, we first
	# check to see how many points we've already been "in alarm".  We only record
	# these alarm points for so long before we just skip them.  After that we'll
	# resume recording them if the sensor value ever drops back out of alarm.
	#
	# Finally, if the current sensor value is NOT in alarm, then we also check
	# the alarm history.  We record a few points after dropping back out of alarm
	# and then close the alarm record by sticking a null value (i.e., None) into
	# the alarm points list.

	if channel.error or channel.stale:
		#Logger.debug("Channel in alarm or stale - no alarms processed")
		return

	ch_config = _loadConfig(channel)
	if not ch_config:
		#Logger.debug("Channel configuration not found - no alarms processed")
		return

	# See if we should record alarms
	if not ch_config.get('recordAlarms', False):
		#Logger.debug("Channel alarm recording is OFF - no alarms processed")
		return

	# all sensors configs (where thresholds are stored)
	sensor_configs = ch_config.get('sensors', None)

	if not sensor_configs:
		#self.Logger.debug("No sensors configured for channel {0}".format(channel.id))
		return 

	# Load previous channel alarms from file
	ch_alarms = _loadAlarms(channel)

	# check each channel sensor value against the thresholds
	for sensor in channel.sensors:

		# get our sensor config by sensor id
		s_config = next((s for s in sensor_configs if s['id'] == sensor.id), None)

		if not s_config:
			#Logger.debug("No sensor configuration found for channel {0}, sensor {1}".format(channel.id, sensor.id))
			continue # no sensor config - skip this sensor

		thresholds = s_config.get('thresholds', [])
		if not thresholds:
			#Logger.debug("No thresholds found for channel {0}, sensor {1}".format(channel.id, sensor.id))
			continue # no thresholds - skip this sensor

		s_alarms = ch_alarms.get(sensor.id, {})

		# check sensor value against thresholds
		for t in thresholds:
			th_value = t.get('value', None)
			direction = t.get('direction', None)
			classification = t.get('classification', None)

			s_value = sensor.values[0]

			# get the alarms for this threshold by classification name
			# if there isn't one, set an empty list as the default
			s_class_alarms = s_alarms.setdefault(classification, [])

			#Logger.debug("Checking [{0}, {1}] for {2}...".format(s_value[0], s_value[1], classification))

			# determine alarm state True or False
			alarm = _checkAlarm(s_value[1], th_value, direction)

			# process point depending on alarm state
			if alarm:
				# point is in alarm
				#COMPARE = 'GREATER' if direction == 'MAX' else 'LESS'
				#Logger.debug("   ...YES! {0} is {1} THAN {2}".format(s_value[1], COMPARE, th_value))

				# pull previous 60 alarm points
				prev_alarm_points = s_class_alarms[-MAX_ALARM_POINTS:]
				#Logger.debug("   Checking previous {0} alarm points...".format(MAX_ALARM_POINTS))

				if not prev_alarm_points[-1]:
					# no previous alarm points, or a new alarm segment
					# create new record w/all sensor buffer values
					#Logger.debug("   ...NO previous alarm point for {0}, so we'll add these points".format(classification))
					alarms_to_add = [[x[0], x[1]] for x in sensor.values if _isNumeric(x[0]) and _isNumeric(x[1])]
					#Logger.debug("alarms to add: {0}".format(alarms_to_add))
					s_class_alarms.extend(alarms_to_add)

				else:
					# previous alarm points - see how far back they are in alarm or until alarm segment break
					#Logger.debug("   Previous alarm points for {0} exist...".format(classification))
					for i, p in enumerate(reversed(prev_alarm_points)):
						if not p or not _checkAlarm(p[1], th_value, direction):
							break

					if i < MAX_ALARM_POINTS:
						#Logger.debug("   ...and fewer than {0} have been recorded, so adding current point".format(MAX_ALARM_POINTS))
						s_class_alarms.extend([ sensor.values[0] ])

			else:
				# point is NOT in alarm
				#Logger.debug("   ...NO!")

				# Loop through previous 5 alarm points and see if they were in alarm
				prev_alarm_points = s_class_alarms[-ALARM_LEAD_POINTS:]
				if prev_alarm_points:

					if len(prev_alarm_points) < ALARM_LEAD_POINTS or \
						any(_checkAlarm(p[1], th_value, direction) for p in prev_alarm_points if p):
						#Logger.debug("Fewer than {0} previous {1} alarms or any of the last {0} were in alarm...".format(ALARM_LEAD_POINTS, classification))

						# Even though we're not in alarm condition, add the point
						# because we haven't been out of alarm for enough points
						s_class_alarms.extend([ sensor.values[0] ])
					else:
						# Close alarm segment if not already closed
						if prev_alarm_points[-1]:
							s_class_alarms.extend([ None ])

				# else we're not in alarm and there are no prior alarm points ... move along

	#Logger.debug("Done processing alarms:")
	#Logger.debug("{0}".format(ch_alarms))
	_saveAlarms(channel, ch_alarms)


def _isNumeric(s):
	try:
		return float(s) == float(s)
	except ValueError:
		return False


def _checkAlarm(value, threshold, d):

	if not _isNumeric(value):
		return False

	d = d.upper()
	if not d in ['MIN', 'MAX']:
		return False

	return ((d == 'MIN' and value < threshold) or (d == 'MAX' and value > threshold))
			

def _loadAlarms(channel):
	global ALARMS_CACHE

	ch_alarms_file = os.path.join(CHDIR, channel.id + '_alarms.json')

	# check for presence of "chX.alarms.reset" file
	ch_alarms_reset = os.path.join(CHDIR, channel.id + '.alarms.reset')

	if os.path.isfile(ch_alarms_reset):
		# remove ch_alarms if it is present
		if os.path.isfile(ch_alarms_file):
			os.remove(ch_alarms_file)
			Logger.info("{0} alarms reset".format(channel.id))
			del ALARMS_CACHE[channel.id]

		# remove the ch reset file
		os.remove(ch_alarms_reset)

	else:

		# read alarms from file to load cache - note that this is
		# only done at startup.  Rest of the time, the cache
		# supplies the alarm history.
		if not ALARMS_CACHE.get(channel.id, None):
			if os.path.isfile(ch_alarms_file):
				with open(ch_alarms_file, 'r') as f:
					ALARMS_CACHE[channel.id] = json.load(f)
			else:
				# alarms file not there yet - add a cache entry
				ALARMS_CACHE.setdefault(channel.id, {})

	return ALARMS_CACHE[channel.id]


# Saves alarms to disk, but only every so often to avoid
# file IO thrashing.  Uses a random delay time since last
# save to try to avoid all channels saving their alarms
# at the same time.
def _saveAlarms(channel, alarms):
	global ALARMS_CACHE

	ch_alarms_file = os.path.join(CHDIR, channel.id + '_alarms.json')

	# if last saved more than 10-20 seconds ago, go ahead and save alarms to disk
	last_saved = ALARMS_CACHE.get(channel.id + '_lastsave', None)
	if not last_saved or time.time() - last_saved > randint(10, 20):
		
		ALARMS_CACHE[channel.id + '_lastsave'] = time.time()

		with LockedOpen(ch_alarms_file, 'a') as fh:
			with tempfile.NamedTemporaryFile('w', dir=os.path.dirname(ch_alarms_file), delete=False) as tf:
				json.dump(alarms, tf, indent="\t")
				tempname = tf.name
			os.replace(tempname, ch_alarms_file)


def _loadConfig(channel):

	global CONFIGS_CACHE

	# get channel configuration filename
	config_file = os.path.join(CHDIR, channel.id + '_config.json')
	config_file_lastmod = os.stat(config_file).st_mtime

	# if there's no config in the CONFIGS cache OR if the modification
	# time has changed on the config file then go ahead and load from file
	if not CONFIGS_CACHE.get(channel.id, None) or CONFIGS_CACHE.get(channel.id + '_lastmod', 0) != config_file_lastmod:
		Logger.debug("Loading channel {0} configuration".format(channel.id))
		# load channel config (if any)
		if os.path.isfile(config_file):
			with open(config_file, 'r') as f:
				CONFIGS_CACHE[channel.id] = json.load(f)
				CONFIGS_CACHE[channel.id + '_lastmod'] = config_file_lastmod

	return CONFIGS_CACHE[channel.id]

