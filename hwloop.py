#!./cme_hw_venv/bin/python

import time, json
import config, memcache

from drivers import Avalanche
from dto_models import Channel

#create shared memory object
sharedmem = memcache.Client(['127.0.0.1:11211'], debug=0)

# setup GPIO
Avalanche = Avalanche()

# setup relay GPIO
print("Initialize Relays")
Avalanche.relayControl(1, True)
Avalanche.relayControl(2, True)
Avalanche.relayControl(3, True)
Avalanche.relayControl(4, True)

print("Sensor boards: Off")
print("SPI bus 0: Disabled")

print("Please wait...")
time.sleep(10);             # give capacitors on sensors boards time to discharge

print("Sensor boards: On")
Avalanche.sensorPower(True)
time.sleep(1);

print("SPI bus 0: Enabled")
Avalanche.spiBus0isolate(False)

print("Setup SPI devices")
Avalanche.setupSpiChannels(config.system['sensors'])

dto_channels = []

print("\nLoop starting...")
while(1):

	# Mark all current DTO channels as stale.
	# We'll freshen the ones we actually read
	# the delete the stale ones in prep to grow
	# and shrink channels as they are added/removed.
	for ch in dto_channels:
		ch.stale = True

	# synchronize sensors - get timestamp for data points
	timestamp = Avalanche.syncSensors()

	# read channel data
	channels = Avalanche.readSpiChannels()

	print "channels read: %r" % channels

	# process Avalanche channels into DTO status channels
	for i, sensors in enumerate(channels):

		# Do we have this channel in our status DTO?
		# TODO: calculate a hash or some means to uniquely identify
		# the channel as configured with its sensors.  Currently
		# we aren't able to add/remove channels dynamically, but we'll
		# probably need to get there.
		# Note that both of these unset the channel 'stale' attribute
		if i <= (len(dto_channels) - 1): # yes - update it
			ch = dto_channels[i] 
			ch.updateSensors(timestamp, sensors)

		else: # no - add it
			ch = Channel(i, timestamp, sensors)
			dto_channels.append(ch)

		# update channel error state from its sensors' errors
		ch['error'] = len([s for s in sensors if s.error]) != 0

	# remove stale channels
	dto_channels = [ch for ch in dto_channels if not ch.stale]

	# update shared memory object
	sharedmem.set('status', json.dumps({ 'channels': dto_channels }))
	#print 'status: %s\n\n' % json.loads(sharedmem.get('status'))

	time.sleep(config.system['loop_freq'])

