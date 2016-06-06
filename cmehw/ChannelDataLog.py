import os, json

class ChannelDataLog(object):
	'''Works like a persistent (to disk) queue (FIFO) to store channel data.

		[ item0, item1, ..., itemN ] << items are added here and removed at left end
			^				   ^
			|				   |
			|				   +----- enqueue (pushes onto queue; if max_size exceeded,
			|							item0 is removed)
			+------------------------ dequeue (pops off of queue; if 'peek=True' just
										returns the value and queue remains unchanged)

		enqueue(item) - push item onto queue (at right end)

		dequeue(peek=False, tail=False) - remove item from queue and return
			its value (at left end); if peek=True item is left on queue
			and value is returned; if tail=True item returned from right
			side of queue instead of left

		flush(peek=False) - clear entire queue returning values;
			if peek=True items are left on queue and values returned
	'''

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
		
	def dequeue(self, peek=False, tail=False):
		if self.size == 0:
			return None

		if not peek or tail:
			lines = self._readlines()

			if not tail:
				result = lines[0]
				self._writelines(lines[1:])
				self.size -= 1
			else:
				result = lines[-1]
			
			return json.loads(result)

		with open(self.path, 'r') as f:
			return json.loads(f.readline())

	def flush(self, peek=False):
		if self.size == 0:
			return None

		result = []
	
		if peek:
			for line in self._readlines():
				result.append(json.loads(line))
			return result

		open(self.path, 'w').close()
		self.size = 0

	
	def enqueue(self, item):

		line = json.dumps(item) + '\n'

		if self.size < self.max_size:
			with open(self.path, 'a') as f:
				f.write(line)

			self.size += 1

		else:
			lines = self._readlines()
			lines = lines[1:]
			lines.append(line)
			self._writelines(lines)

	# Private methods

	def __len__(self):
		return self.size

	def _readlines(self):
		with open(self.path, 'r') as f:
			return f.readlines()

	def _writelines(self, lines):
		with open(self.path, 'w') as f:
			for line in lines:
				f.write(line)

