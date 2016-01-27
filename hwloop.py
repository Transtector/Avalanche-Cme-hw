#!./cme_hw_venv/bin/python

import time, json
import config, memcache

from Avalanche import Avalanche
from Models import Channel

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
Avalanche.setupSpiChannels(config.SPI_SENSORS)

dto_channels = []

spinners = "|/-\\"
spinner_i = 0
while(1):
	# Console output for piece of mind
	sys.stdout.write("Hardware looping %s\r" % (spinners[spinner_i]) )
	sys.stdout.flush()
	spinner_i = (spinner_i + 1) % len(spinners)

	# Show Loop operation via Heartbeat LED
	Avalanche.ledToggle(5)

	# Mark all current DTO channels as stale.
	# We'll freshen the ones we actually read
	# then delete the stale ones in prep to grow
	# and shrink channels as they are added/removed.
	for ch in dto_channels:
		ch.stale = True

	# synchronize sensors - get timestamp for data points
	timestamp = Avalanche.syncSensors()

	# read channel data
	channels = Avalanche.readSpiChannels()

	# process Avalanche channels into DTO status channels
	for i, channel in enumerate(channels):

		# Do we have this channel in our status DTO?
		# TODO: calculate a hash or some means to uniquely identify
		# the channel as configured with its sensors.  Currently
		# we aren't able to add/remove channels dynamically, but we'll
		# probably need to get there.
		# Note that both of these unset the channel 'stale' attribute
		# and may set the channel 'error' string.
		if i > (len(dto_channels) - 1): # not found - create it
			chId = 'ch' + str(i)
			ch = Channel(chId, channel.error, timestamp, channel.sensors)
			dto_channels.append(ch)

		else: # channel already created - just get a ref
			ch = dto_channels[i]

		# Update the channel with new values - this also logs the values to disk
		ch.updateSensors(channel.error, timestamp, channel.sensors)

	# remove stale channels
	dto_channels = [ch for ch in dto_channels if not ch.stale]

	# update shared memory object
	sharedmem.set('status', json.dumps({ 'channels': dto_channels }))

	time.sleep(config.LOOP_PERIOD_s)
