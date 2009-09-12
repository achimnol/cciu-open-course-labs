# -*- coding: utf-8 -*-

# Copyright 2009, NexR (http://nexr.co.kr)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import with_statement
import os, sys
from StringIO import StringIO

class StdoutCollector():
	"""
	This class is for unit-testing with some standard output.

	Usage:
	>>> output = StringIO()
	>>> with StdoutCollector(output):
	...		print 'blah blah blah'
	>>> output.getvalue().strip() == 'blah blah blah'
	True

	Note that python's internal print statement adds a newline character
	at the end of each output.
	"""

	def __init__(self, writer):
		# writer should have write() method like file objects.
		self.writer = writer

	def __enter__(self):
		self.old_stdout = sys.stdout
		sys.stdout = self.writer

	def __exit__(self, type, value, traceback):
		sys.stdout = self.old_stdout

if __name__ == '__main__':
	import doctest
	doctest.testmod()
