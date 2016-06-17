import sys, os, json, threading
import config


class Channel(dict):

	def __init__(self, id, hw_ch):
		
		# class attributes don't show up in the serialization
		# but get used for manipulations (finding, filtering, etc)
		self.id = id
		self.hw_ch = hw_ch
		self.error = hw_ch.error
		self.stale = False

		# dict keys that will get serialized for data transfers
		self['id'] = id
		self['error'] = hw_ch.error
		self['stale'] = self.stale
		self['sensors'] = [ Sensor('s' + str(i), sensor) for i, sensor in enumerate(hw_ch.sensors) ]
		self['controls'] = []

	def debugPrint(self):
		if self['error']:
			msg = "ERROR"
		else:
			msg = ", ".join([ "[ {0}, {1} :: {2} ]".format(s['id'], s['unit'], self.hw_ch.sensors[i].value ) for i, s in  enumerate(self['sensors']) ])

			if self['stale']:
				msg += " (STALE)"

		return "{{{0}: {1}}}".format(self.id, msg)


class Sensor(dict):
	def __init__(self, id, hw_sensor):
		self['id'] = self.id = id
		self['type'] = self.type = hw_sensor.type
		self['unit'] = self.unit = hw_sensor.unit
		self['value'] = self.value = hw_sensor.value


class Control(dict):
	def __init__(self, id, hw_control):
		self['id'] = self.id = id
		self['type'] = self.type = hw_control.type
		self['state'] = self.state = hw_control.state
