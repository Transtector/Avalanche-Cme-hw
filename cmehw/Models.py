

class Channel():

	def __init__(self, id, hw_ch):
		
		# class attributes don't show up in the serialization
		# but get used for manipulations (finding, filtering, etc)
		self.id = id
		self.hw_ch = hw_ch
		self.error = hw_ch.error
		self.stale = False

		self.sensors = [ Sensor('s' + str(i), s) for i, s in enumerate(hw_ch.sensors) ]
		self.controls = []

	def debugPrint(self):
		if self.error:
			msg = "ERROR"
		else:
			msg = ", ".join([ "{0} = {1} {2}".format(s.id, s.value, s.unit) for s in self.sensors ])

			if self.stale:
				msg += " (STALE)"

		return "{{ {0}: {1} }}".format(self.id, msg)


class Sensor():
	def __init__(self, id, hw_sensor):
		self._hw = hw_sensor

		self.id = id
		self.type = self._hw.type
		self.unit = self._hw.unit

	@property
	def value(self):
		return self._hw.value


class Control(dict):
	def __init__(self, id, hw_control):
		self._hw = hw_control

		self.id = id
		self.type = self._hw.type
		self.state = self._hw.state
