#
# Copyright (C) 2010 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.

import unittest
from builder.imagebuilderinterface import ImageBuilderInterface
from builder.mockbuilder import MockBuilder


class TestmMockBuilder(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def testImplementsImageBuilderInterface(self):
		self.assert_(ImageBuilderInterface.implementedBy(MockBuilder), 'MockBuilder does not implement the ImageBuilder interface...')
	
	def testInit(self):
		mock_builder = MockBuilder("IDL")
		self.assertEqual("IDL", mock_builder.template)
		self.assert_(mock_builder.image_id, 'Initilizer failed to set \'image_id\'...')
    
if __name__ == '__main__':
	unittest.main()