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

