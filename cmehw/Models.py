import sys, os, json, threading
import config


class Channel(dict):

	def __init__(self, id, hw_ch):
		
		# class attributes don't show up in the serialization
		# but get used for manipulations (finding, filtering, etc)
		self.id = id
		self.hw_ch = hw_ch
		self.stale = False
		self.busy = False

		# dict keys that will get serialized for data transfers
		self['id'] = id
		self['stale'] = self.stale
		self['error'] = hw_ch.error
		self['sensors'] = [ Sensor('s' + str(i), sensor.type, sensor.unit) for i, sensor in enumerate(hw_ch.sensors) ]
		self['controls'] = []


	def publish(self):
		self['error'] = self.hw_ch.error


	def debugPrint(self):
		if self['error']:
			msg = "ERROR"
		else:
			msg = ", ".join([ "[ {0}, {1} :: {2} ]".format(s['id'], s['unit'], self.hw_ch.sensors[i].value ) for i, s in  enumerate(self['sensors']) ])

			if self['stale']:
				msg += " (STALE)"

		return "{{{0}: {1}}}".format(self.id, msg)


class Sensor(dict):
	def __init__(self, id, sensorType, unit):
		self['id'] = id
		self['type'] = sensorType
		self['unit'] = unit
		self['data'] = []


class Control(dict):
	def __init__(self, id, controlType):
		self['id'] = id
		self['type'] = controlType
		self['data'] = []
