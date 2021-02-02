## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2016, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2021 SURF https://www.surf.nl
# Copyright (C) 2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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
        self.assertEqual('1s', self.services.niceTime(1))
        self.assertEqual('1s', self.services.niceTime(1.3))
        self.assertEqual('112s', self.services.niceTime(112.234))
        self.assertEqual('2m  3s', self.services.niceTime(123.23))
        self.assertEqual('2m 14s', self.services.niceTime(134.23))
        self.assertEqual('1h  0m', self.services.niceTime(3602.3))
        self.assertEqual('2 days 1h 13m', self.services.niceTime(177180.3))
        self.assertEqual('?', self.services.niceTime(None))
