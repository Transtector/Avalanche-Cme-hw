import os, json, time

import sqlite3


from .common import Config

# Alarms database
ALARMS = Config.PATHS.ALARMS_DB



class Singleton(type):
	_instances = {}
	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instances[cls]



class LockableCursor:
	def __init__(self, cursor):
		self.cursor = cursor
		self.lock = threading.Lock()

	def execute(self, arg0, arg1=None):
		self.lock.acquire()

		try:
			#print("{}".format(arg1 if arg1 else arg0))
			
			if arg1:
				result = []

			self.cursor.execute(arg1 if arg1 else arg0)

			if arg1:
				if arg0 == 'all':
					result = self.cursor.fetchall()
				elif arg0 == 'one':
					result = self.cursor.fetchone()

		except Exception as e:
			raise e

		finally:
			self.lock.release()
			if arg1:
				return result

	def executemany(self, arg0, arg1):
		self.lock.acquire()

		try:
			self.cursor.executemany(arg0, arg1)

		except Exception as e:
			raise e

		finally:
			self.lock.release()



class AlarmManager(metaclass=Singleton):

	_connection = None
	_cursor = None

	def __init__(self):

		def dictFactory(cursor, row):
			aDict = {}
			for iField, field, in enumerate(cursor.description):
				aDict[field[0]] = row[iField]
			return aDict

		if not self._connection:
			self._connection = sqlite3.connect(ALARMS, check_same_thread = False)
			self._connection.row_factory = dictFactory
			self._connection.text_factory = str
			self._cursor = LockableCursor(self._connection.cursor())

			# Create the alarms table if it's not already there
			# Use columns:
			#	start (INT) - start time of alarm in Unix timestamp (milliseconds)
			#	end (INT) - end time of of alarm (if any) in Unix timestamp (milliseconds)
			#	source_channel (TEXT) - channel id of the alarm trigger source (e.g., 'ch0')
			#	source_sensor (TEXT) - sensor id of the alarm trigger source (e.g., 's0')
			#	type (TEXT) - classification string for the type of alarm (e.g., 'SAG')
			#	data (TEXT) - waveform data in JSON object string that can be stored with the alarm
			self._cursor.execute('''CREATE TABLE IF NOT EXISTS alarms 
				(id INTEGER PRIMARY KEY, channel TEXT, sensor TEXT, type TEXT, start_ms INT, end_ms INT, step_ms INT, data TEXT)''')


	def __del__(self):

		self._connection.close()


	def InsertAlarm(self, raw_data OR Alarm_object):

		alarms = []

		for c in range(0, count):

			# start randomly some days * hours * milliseconds before now
			start_ms = int(round(time.time() * 1000)) - random.randint(1, 2) * random.randint(1, 23) * random.randint(1, 3599999)

			# end 1 - 5 minutes after start, but no greater than now
			end_ms = start_ms + random.randint(1, 4) * 60 * 1000 + random.randint(0, 59) * 1000 + random.randint(0, 999)
			end_ms = min(time.time() * 1000, end_ms)

			# generate fake waveform data for the alarms
			sample_rate = 7.8125 * 1000 # 7.8125 kHz
			sample_period = 50 * 0.001 # 50 ms
			samples = math.ceil(sample_rate * sample_period)

			# Generates the format [ [ t0, Va, Vb, Vc, PI ], [t1, Va, Vb, Vc, PI ], ... [tN, Va, Vb, Vc, PI ] ]
			def gen_fake_phases(amplitude_rms, frequency_hz):

				def sin(amp_rms, t_seconds, phi_degrees):

					return amp_rms * math.sqrt(2) * math.sin(2 * math.pi * frequency_hz * t_seconds / sample_rate + math.radians(phi_degrees))

				def pib(phA, phB, phC):
					phAVG = ( phA + phB + phC ) / 3
					phMAX = max([ abs(phAVG - phA), abs(phAVG - phB), abs(phAVG - phC) ])

					if phAVG:
						return 100 * ( phMAX / phAVG )
					else:
						return 0

				result = []
				for t in range(0, samples):
					sample_time = t / sample_rate

					PHA_AMP = amplitude_rms + 0.05 * amplitude_rms * (0.5 - random.random())
					PHB_AMP = amplitude_rms + 0.05 * amplitude_rms * (0.5 - random.random())
					PHC_AMP = amplitude_rms + 0.05 * amplitude_rms * (0.5 - random.random())

					PHA = sin(PHA_AMP, t, 0)
					PHB = sin(PHB_AMP, t, 120)
					PHC = sin(PHC_AMP, t, 240)
					PIB = pib(PHA_AMP, PHB_AMP, PHC_AMP)

					result.append([ sample_time, PHA, PHB, PHC, PIB ])

				return result

			input_voltages_and_PI_START = gen_fake_phases(208, 60)
			input_voltages_and_PI_END = gen_fake_phases(208, 60)

			output_voltages_and_PI_START = gen_fake_phases(277, 60)
			output_voltages_and_PI_END = gen_fake_phases(277, 60)
			
			output_currents_START = gen_fake_phases(90, 60)
			output_currents_END = gen_fake_phases(90, 60)

			# Which channel will trigger? (don't include the current channels which use s1)
			alarm_ch = "ch" + str(random.randint(0, 7))

			# Slice the generated data to individual channel/sensors
			a = {
				"channel": alarm_ch,
				"sensor": "s0",
				"type": "FAKE",
				"start_ms": start_ms,
				"end_ms": end_ms,
				"step_ms": 1 / sample_rate,
				"data": {
					"ch0": {
						"s0": [ V[1] for V in input_voltages_and_PI_START ] + [ V[1] for V in input_voltages_and_PI_END ]
					},
					"ch1": {
						"s0": [ V[2] for V in input_voltages_and_PI_START ] + [ V[2] for V in input_voltages_and_PI_END ]
					},
					"ch2": {
						"s0": [ V[3] for V in input_voltages_and_PI_START ] + [ V[3] for V in input_voltages_and_PI_END ]
					},
					"ch3": {
						"s0": [ V[4] for V in input_voltages_and_PI_START ] + [ V[4] for V in input_voltages_and_PI_END ]
					},
					"ch4": {
						"s0": [ V[1] for V in output_voltages_and_PI_START ] + [ V[1] for V in output_voltages_and_PI_END ],
						"s1": [ V[1] for V in output_currents_START ] + [ V[1] for V in output_currents_END ]
					},
					"ch5": {
						"s0": [ V[2] for V in output_voltages_and_PI_START ] + [ V[2] for V in output_voltages_and_PI_END ],
						"s1": [ V[2] for V in output_currents_START ] + [ V[2] for V in output_currents_END ]
					},
					"ch6": {
						"s0": [ V[3] for V in output_voltages_and_PI_START ] + [ V[3] for V in output_voltages_and_PI_END ],
						"s1": [ V[3] for V in output_currents_START ] + [ V[3] for V in output_currents_END ]
					},
					"ch7": {
						"s0": [ V[4] for V in output_voltages_and_PI_START ] + [ V[4] for V in output_voltages_and_PI_END ] 
					}
				}
			}

			# Make the alarm a tuple of the fields
			alarms.append( (a['channel'], a['sensor'], a['type'], a['start_ms'], a['end_ms'], a['step_ms'], json.dumps(a['data'])) )

		self._cursor.executemany('INSERT INTO alarms(channel, sensor, type, start_ms, end_ms, step_ms, data) VALUES(?, ?, ?, ?, ?, ?, ?)', alarms)
		self._connection.commit()
		return count




class Alarm():
	''' Alarm object holds information about alarms processed by the hardware.
	'''
	my_new_alarm = {}
	my_new_alarm['channel'] = 'ch0'
	my_new_alarm['sensor'] = 's0'
	my_new_alarm['type'] = 'SAG'
	my_new_alarm['start_ms'] = time.time() * 1000
	my_new_alarm['end_ms'] = time.time() * 1000
	my_new_alarm['step_ms'] = 0.512 # 512 us sample rate

	my_new_alarm['data'] = {
		"ch0": {
			"s0": [ V[1] for V in input_voltages_and_PI_START ] + [ V[1] for V in input_voltages_and_PI_END ]
		},
		"ch1": {
			"s0": [ V[2] for V in input_voltages_and_PI_START ] + [ V[2] for V in input_voltages_and_PI_END ]
		},
		"ch2": {
			"s0": [ V[3] for V in input_voltages_and_PI_START ] + [ V[3] for V in input_voltages_and_PI_END ]
		},
		"ch3": {
			"s0": [ V[4] for V in input_voltages_and_PI_START ] + [ V[4] for V in input_voltages_and_PI_END ]
		},
		"ch4": {
			"s0": [ V[1] for V in output_voltages_and_PI_START ] + [ V[1] for V in output_voltages_and_PI_END ],
			"s1": [ V[1] for V in output_currents_START ] + [ V[1] for V in output_currents_END ]
		},
		"ch5": {
			"s0": [ V[2] for V in output_voltages_and_PI_START ] + [ V[2] for V in output_voltages_and_PI_END ],
			"s1": [ V[2] for V in output_currents_START ] + [ V[2] for V in output_currents_END ]
		},
		"ch6": {
			"s0": [ V[3] for V in output_voltages_and_PI_START ] + [ V[3] for V in output_voltages_and_PI_END ],
			"s1": [ V[3] for V in output_currents_START ] + [ V[3] for V in output_currents_END ]
		},
		"ch7": {
			"s0": [ V[4] for V in output_voltages_and_PI_START ] + [ V[4] for V in output_voltages_and_PI_END ] 
		}
	}




	def __init__(self, alarm=None):

		if not alarm:
			self.id = 1
			self.channel = 'ch0'
			self.sensor = 's0'
			self.type = 'UNKNOWN'
			self.start_ms = int(round(time.time() * 1000))
			self.end_ms = None
			self.step_ms = 0.128
			self.data = None

		else:
			self.id = alarm['id']
			self.channel = alarm['channel']
			self.sensor = alarm['sensor']
			self.type = alarm['type']
			self.start_ms = alarm['start_ms']
			self.end_ms = alarm['end_ms']
			self.step_ms = alarm['step_ms']
			self.data = json.loads(alarm['data'])

	def __repr__(self):
		return "Alarm[{}]:({}, {}, {}, {}, {}, {}, data[{}])".format(self.id, self.channel, self.sensor, self.type, self.start_ms, self.end_ms, self.step_ms, len(self.data['ch0']['s0']) if self.data else 0)

