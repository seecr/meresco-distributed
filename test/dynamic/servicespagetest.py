## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2016 Seecr (Seek You Too B.V.) http://seecr.nl
#
# This file is part of "Meresco Distributed"
#
# "Meresco Distributed" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Distributed" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Distributed"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from seecr.test import SeecrTestCase, CallTrace
from meresco.html import DynamicHtml
from meresco.distributed import dynamicPath

class ServicesPageTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        reactor = CallTrace('reactor')
        self.dynamicHtml = DynamicHtml([dynamicPath], reactor, watch=False)
        self.services = self.dynamicHtml.getModule('_services')

    def testNiceTime(self):
        self.assertEquals('1s', self.services.niceTime(1))
        self.assertEquals('1s', self.services.niceTime(1.3))
        self.assertEquals('112s', self.services.niceTime(112.234))
        self.assertEquals('2m  3s', self.services.niceTime(123.23))
        self.assertEquals('2m 14s', self.services.niceTime(134.23))
        self.assertEquals('1h  0m', self.services.niceTime(3602.3))
        self.assertEquals('2 days 1h 13m', self.services.niceTime(177180.3))
        self.assertEquals('?', self.services.niceTime(None))
