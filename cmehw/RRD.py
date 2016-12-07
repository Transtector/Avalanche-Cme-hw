import os, glob, sys, time, random
import rrdtool
import Config

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
RRDCACHED_ADDRESS = Config.RRDCACHED_ADDRESS

# this is an rrd that's created at init to ensure the RRD system
# is working properly.  Note that the full path to the file is not
# given, as that should be handled (encapsulated) by the cache daemon
# service.  In a pinch (i.e., if the cache layer is not working properly)
# the path to the RRD files is visible to all layers and resides in the
# /data/log folder.
TESTRRD = "test.rrd"

# Inherit from the rrdtool.OperationalError exception
# to create our own wrapper here.
class RRD_ERROR(rrdtool.OperationalError):
	''' handle some RRD errors '''
	pass

class RRD():

	def __init__(self):
		''' Verify connection to rrdcached on init
		'''
		from Logging import Logger

		self._logger = Logger # get main logger
		self._logger.info("Setting up RRD")

		start_time = time.time()

		# this is supposed to use the rrdcached service to
		# create the test.rrd file in CHDIR, but if the
		# service is not running properly will silently fail
		# and create the test.rrd file in the cmehw folder.
		# We'll test for that condition and exit with error
		# if the test.rrd file is found in our program folder
		# and NOT found in CHDIR.
		rrdtool.create(TESTRRD, '-d', RRDCACHED_ADDRESS,
			'--step', '1', 
			'DS:index:GAUGE:10:0:100',
			'DS:random:GAUGE:10:0:100',
			'RRA:LAST:0.5:1:10')

		# if test.rrd exists in our APPROOT folder
		BAD_RRD = os.path.join(Config.APPROOT, TESTRRD)
		if os.path.exists(BAD_RRD):
			# delete the bad test.rrd
			os.remove(BAD_RRD)

			# log the issue
			err_msg = 'Invalid RRDCacheD {0} creation - is RRDCacheD running on {1}?'.format(TESTRRD, RRDCACHED_ADDRESS)
			self._logger.error(err_msg)

			# raise an exception
			raise RRD_ERROR(err_msg)


		# Now we try to update the test.rrd with some random data points
		# this may also fail if something is wrong with rrdcached, but at
		# least will report something reasonable in the exception.
		t = 0
		while (t < 10):
			rrdtool.update(TESTRRD, '-d', RRDCACHED_ADDRESS,
				'N:{0}:{1}'.format(t, random.randint(0, 100)))
			t = t + 1
			time.sleep(1)

		# TODO: check the results (somehow).  If the RRD doesn't
		# init properly, then there's no point to continue (I think),
		# so we'd fire an exception and terminate the cmehw main program.
		self._test = rrdtool.fetch(TESTRRD, '-d', RRDCACHED_ADDRESS,
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
		ch_rrd = glob.glob(os.path.join(Config.CHDIR, channel.id + '_*.rrd'))

		if ch_rrd:
			ch_rrd = ch_rrd[0] # full path to first match


		# check for presence of "chX.rrd.reset" file
		ch_rrd_reset = os.path.isfile(os.path.join(Config.CHDIR, channel.id + '.rrd.reset'))

		if ch_rrd_reset:
			# remove ch_rrd if it is present
			if ch_rrd:
				os.remove(ch_rrd)
				self._logger.info("RRD {0} removed to reset".format(os.path.basename(ch_rrd)))
				ch_rrd = None

			# remove the ch reset file			
			os.remove(os.path.join(Config.CHDIR, channel.id + '.rrd.reset'))


		if not ch_rrd:
			# Channel RRD not found or was reset create it.
			# One DS for every sensor in the channel.

			# embed first publish time in the RRD filename
			ch_rrd = channel.id + '_' + str(int(time.time())) + '.rrd'

			DS = []
			for s in channel.sensors:
				# TODO: get the min/max sensor values from the sensor
				# and replace the "U" (unknowns) in the DS definition.
				
				# NOTE: from rrdtool.org that ds_name must be from 1 to
				# 19 characters long in the characters [a-zA-Z0-9_].
				ds_name = "_".join([ s.id, s.type, s.unit ])

				self._logger.info("RRD adding DS {0}".format(ds_name))
				
				DS.append("DS:" + ds_name + ":GAUGE:10:U:U")

			# Add RRA's (anticipating 400 point (pixel) outputs for plotting)
			RRA = [ 
				# real-time - every point for 2 hours (3600 points/hour)
				"RRA:LAST:0.5:1:{:d}".format( 2 * 3600 ),

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
				"RRA:MAX:0.5:1d:{:d}".format( 1 * 365 ) ]

			rrdtool.create(ch_rrd, '-d', RRDCACHED_ADDRESS, '--step', '1', *(DS + RRA) )

			self._logger.info("RRD created for {0}".format(channel.id))

		else:
			# ensure ch_rrd is filename only at this point
			ch_rrd = os.path.basename(ch_rrd)

		# Update the channel's RRD
		DATA_UPDATE = 'N:' + ':'.join([ '{:f}'.format(s.value) for s in channel.sensors ])

		#self._logger.debug("RRD update: " + DATA_UPDATE) 

		# try/catch to watch out for updates that occur too often.  Here we just
		# log then ignore the exception (for now)
		try:
			rrdtool.update(ch_rrd, '-d', RRDCACHED_ADDRESS, DATA_UPDATE)

		except:
			self._logger.error(sys.exc_info()[1])
