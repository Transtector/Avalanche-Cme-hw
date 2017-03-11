import os, glob, sys, time, random, re
import rrdtool

from .common import Config

# The location where channel data and configuration are stored (typically /data/channels/)
CHDIR = Config.PATHS.CHDIR

'''
Notes:

The rrdtool uses a daemon (variously called 'rrdtool-cached' or 'rrdcached' depending on the 
particular software distro under which it's used) service to process reads and writes to/from
the RRD files.

While technically, the CME implmentation does not currently require a separate service to
handle RRD processing, there are several advantages to doing so.  First, the cache service
creates a more robust and fault-tolerant system (e.g., yank the power plug while data is
being logged to RRD), and can gracefully recover RRD data that might otherwise get corrupted.
Next, having the RRD cached service in its own docker layer creates a great spot to manage
the input/output data logging system from the software update perspective.  As the layers are
loosely coupled, we can more easily replace layer contents with newer/better/working software
without greatly impacting the other layers.
'''
RRDCACHED = Config.RRD.RRDCACHED

# This is an rrd that's created at init to ensure the RRD system
# is working properly.  Note that the full path to the file is not
# given, as that should be handled (encapsulated) by the cache daemon
# service.  In a pinch (i.e., if the cache layer is not working properly)
# the path to the RRD files is visible to all layers and resides in the
# CHDIR folder.
TESTRRD = os.path.join(CHDIR, "test.rrd")


# Inherit from the rrdtool.OperationalError exception
# to create our own wrapper here.
class RRD_ERROR(rrdtool.OperationalError):
	''' handle some RRD errors '''
	pass

# these are rrdtool wrappers that use the RRDCacheD (or not)
def _rrdcreate(rrdfile, *args):
	if RRDCACHED:
		return rrdtool.create(rrdfile, '-d', RRDCACHED, *args)

	return rrdtool.create(os.path.join(CHDIR, rrdfile), *args)

def _rrdupdate(rrdfile, *args):
	if RRDCACHED:
		return rrdtool.update(rrdfile, '-d', RRDCACHED, *args)

	return rrdtool.update(os.path.join(CHDIR, rrdfile), *args)

def _rrdfetch(rrdfile, *args):
	if RRDCACHED:
		return rrdtool.fetch(rrdfile, '-d', RRDCACHED, *args)

	return rrdtool.fetch(os.path.join(CHDIR, rrdfile), *args)


class RRD():

	def __init__(self):
		''' Verify connection to rrdcached on init
		'''
		from .Logging import Logger

		self._logger = Logger # get main logger
		self._logger.info("\nSetting up RRD")

		start_time = time.time()

		# this is supposed to use the rrdcached service to
		# create the test.rrd file in CHDIR, but if the
		# service is not running properly will silently fail
		# and create the test.rrd file in the cmehw folder.
		# We'll test for that condition and exit with error
		# if the test.rrd file is found in our program folder
		# and NOT found in CHDIR.
		_rrdcreate(TESTRRD,
			'--step', '1', 
			'DS:index:GAUGE:10:0:100',
			'DS:random:GAUGE:10:0:100',
			'RRA:LAST:0.5:1:10')

		# if test.rrd exists in our APPROOT folder
		'''  JJB:  Commented out for use w/o RRDCacheD
		BAD_RRD = os.path.join(Config.PATHS.APPROOT, TESTRRD)
		if os.path.exists(BAD_RRD):
			# delete the bad test.rrd
			os.remove(BAD_RRD)

			# log the issue
			err_msg = 'Invalid RRDCacheD {0} creation - is RRDCacheD running on {1}?'.format(TESTRRD, RRDCACHED)
			self._logger.error(err_msg)

			# raise an exception
			raise RRD_ERROR(err_msg)
		'''
		
		# Now we try to update the test.rrd with some random data points
		# this may also fail if something is wrong with rrdcached, but at
		# least will report something reasonable in the exception.
		t = 0
		while (t < 10):
			_rrdupdate(TESTRRD, 'N:{0}:{1}'.format(t, random.randint(0, 100)))
			t = t + 1
			time.sleep(1)

		# TODO: check the results (somehow).  If the RRD doesn't
		# init properly, then there's no point to continue (I think),
		# so we'd fire an exception and terminate the cmehw main program.
		self._test = _rrdfetch(TESTRRD,
			'LAST',
			'--start', str(int(start_time)),
			'--end', str(int(time.time())))

		self._logger.info("RRD setup finished")


	def publish(self, channel):
		''' Publish channel data to an RRD.  Each sensor in the channel is assigned a DS (data source)
			in the RRD.

			Channel RRD's are created if necessary using the filename convention:

				chx(y)_<timestamp>.rrd

			where y is used if more than channels 0..9 and timestamp is from int(time.time()).

			Publish will recreate an (fresh/empty) RRD if the following 'reset' file found:

				chx(y).rrd.reset

			and the reset file will be deleted after new RRD created.
		'''

		# Just return if channel is in error or stale (means no RRD's are created if the 
		# channel starts out in error condition).
		if channel.error or channel.stale:
			return

		# Use glob to find existing RRD for chX (this might result in None)
		ch_rrd = glob.glob(os.path.join(CHDIR, channel.id + '_*.rrd'))

		if ch_rrd:
			ch_rrd = ch_rrd[0] # full path to first match

		# check for presence of "chX.rrd.reset" file
		ch_rrd_reset = os.path.join(CHDIR, channel.id + '.rrd.reset')

		if os.path.isfile(ch_rrd_reset):
			# remove ch_rrd if it is present
			if ch_rrd:
				os.remove(ch_rrd)
				self._logger.info("RRD {0} removed to reset".format(os.path.basename(ch_rrd)))
				ch_rrd = None

			# remove the ch reset file			
			os.remove(ch_rrd_reset)

		if not ch_rrd:
			# Channel RRD not found or was reset. (Re)create it here.
			# One DS for every sensor in the channel.

			# embed first publish time in the RRD filename
			ch_rrd = channel.id + '_' + str(int(time.time())) + '.rrd'

			DS = []
			for k, s in channel.sensors.items():
				# TODO: get the min/max sensor values from the sensor
				# and replace the "U" (unknowns) in the DS definition.
				
				# NOTE: from rrdtool.org that ds_name must be from 1 to
				# 19 characters long in the characters [a-zA-Z0-9_].
				regex = re.compile('[^a-zA-Z0-9_]')
				clean_type = regex.sub('_', s.type)[:3]
				clean_unit = regex.sub('_', s.unit)[:3]
				ds_name = "_".join([ s.id, clean_type, clean_unit ])

				if len(s.range) > 0:
					ds_range = ":{0}:{1}".format(s.range[0], s.range[1])
				else:
					ds_range = ":U:U"

				ds = "DS:" + ds_name + ":GAUGE:10" + ds_range
				DS.append(ds)
				self._logger.info("\tRRD sensor DS added {0}".format(ds))

			RRA = []
			for rra in channel.rra.values():
				for r in rra:
					RRA.append(r)

			'''
			# Add RRA's (anticipating 400 point (pixel) outputs for plotting)
			RRA = [ 
				# live - every point for 15 minutes (3600 points/hour, 900 points/15 min)
				"RRA:LAST:0.5:1:{:d}".format( 2 * 900 ),

				# daily - 5 minute stats for a day (12 5m blocks per hour)
				"RRA:AVERAGE:0.5:5m:{:d}".format( 12 * 24 ),
				"RRA:MIN:0.5:5m:{:d}".format( 12 * 24 ),
				"RRA:MAX:0.5:5m:{:d}".format( 12 * 24 ),

				# weekly - 30 minute stats for 7 days (48 30m blocks per day)
				"RRA:AVERAGE:0.5:30m:{:d}".format( 48 * 7 ),
				"RRA:MIN:0.5:30m:{:d}".format( 48 * 7 ),
				"RRA:MAX:0.5:30m:{:d}".format( 48 * 7 ),
 
				# monthly - 2 hour stats for 31 days (12 2h blocks per day)
				"RRA:AVERAGE:0.5:2h:{:d}".format( 12 * 31 ),
				"RRA:MIN:0.5:2h:{:d}".format( 12 * 31 ),
				"RRA:MAX:0.5:2h:{:d}".format( 12 * 31 ),

				# yearly - 1 day stats for 365 days
				"RRA:AVERAGE:0.5:1d:{:d}".format( 1 * 365 ),
				"RRA:MIN:0.5:1d:{:d}".format( 1 * 365 ),
				"RRA:MAX:0.5:1d:{:d}".format( 1 * 365 )
			]
			'''

			# Note: be careful here - the last argment here *(DS + RRA) requires a
			# list of str.  Loading configs from file that make their way here can
			# result in unicode items. See http://stackoverflow.com/q/956867.
			ds_and_rra = [ str(s) for s in (DS + RRA) ]
			_rrdcreate(ch_rrd, '--step', '1', *ds_and_rra )
			self._logger.info("RRD {0} created".format(os.path.basename(ch_rrd)))

		else:
			# ensure ch_rrd is a filename only at this point
			ch_rrd = os.path.basename(ch_rrd)

		# Create the update argument for the channel's RRD
		DATA_UPDATE = 'N:' + ':'.join([ '{:f}'.format(s.values[0][1]) for s in channel.sensors.values() ])

		#self._logger.debug("RRD update: " + DATA_UPDATE) 

		# try/catch to watch out for updates that occur too often.  Here we just
		# log and ignore the exception (for now).  This may just be related to
		# an issue with the RRDCacheD and floating point rounding errors.
		try:
			_rrdupdate(ch_rrd, DATA_UPDATE)

		except:
			self._logger.error(sys.exc_info()[1])
