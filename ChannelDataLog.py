import os, json

class ChannelDataLog(object):
	'''Works like a persistent (to disk) queue to store channel data'''

	def __init__(self, path, max_size=10):
		self.path = path
		self.max_size = max_size

		size = 0
		if os.path.exists(path):
			lines = self._readlines()
			size = len(lines)

		else:
			open(self.path, 'w').close()

		if size > max_size:
			self._writelines(lines[(size - max_size):])
			size = max_size

		self.size = size

	
	def peek(self):
		if self.size == 0:
			return None
		
		with open(self.path, 'r') as f:
			return json.loads(f.readline())	
	
	def peekAll(self, max_points):
		if self.size == 0:
			return None

		lines = self._readlines()
		decimate = len(lines) > max_points

		if decimate:
			bucket_size = (len(lines) - 2) // (max_points - 2) # floor quotient
			data_size = max_points
		else:
			bucket_size = 1
			data_size = len(lines)

		data = []

		# first points
		data.append(json.loads(lines[0]))

		# points in between may get decimated into bins of 'bucket_size' where max values are chosen
		for i in range(1, data_size - 1):
			r = (i - 1) * bucket_size + 1

			bucket=[]
			for line in lines[r:r+bucket_size]:

				if len(bucket) == 0:
					bucket = json.loads(line)

				elif decimate:
					newline = json.loads(line)
					for j in range(1, len(bucket)):
						if bucket[j] < newline[j]:
							bucket[j] = newline[j]


			data.append(bucket)

		# last points
		data.append(json.loads(lines[-1]))

		return data

	def push(self, data):

		line = json.dumps(data) + '\n'

		if self.size < self.max_size:
			with open(self.path, 'a') as f:
				f.write(line)

			self.size += 1

		else:
			lines = self._readlines()
			lines = lines[1:]
			lines.append(line)
			self._writelines(lines)

	def clear(self):
		if self.size == 0: 
			return
		open(self.path, 'w').close()
		self.size = 0

	def pop(self):
		if self.size == 0:
			return None

		lines = self._readlines()
		self._writelines(lines[1:])
		
		self.size -= 1

		return json.loads(lines[0])

	
	def __len__(self):
		return self.size


	def _readlines(self):
		with open(self.path, 'r') as f:
			return f.readlines()

	
	def _writelines(self, lines):
		with open(self.path, 'w') as f:
			for line in lines:
				f.write(line)

