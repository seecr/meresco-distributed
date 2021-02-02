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

from meresco.core import Observable
from meresco.distributed import ServiceGroup, Service
from weightless.core import be
from time import time

class ServiceGroupTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.services = {}
        self.observer = CallTrace(methods=dict(listServices=lambda **kwargs: self.services))
        self.top = be((Observable(),
            (ServiceGroup(),
                (self.observer,)
            )
        ))
        for i in range(1,4):
            self.addService('id{0}'.format(i), number=i, type='b')
        for i in range(4,6):
            self.addService('id{0}'.format(i), number=i, type='a')

    def testTransparent(self):
        self.assertEqual(set(['id1', 'id2', 'id3', 'id4', 'id5']), set(self.top.call.listServices().keys()))

    def testIpGrouping(self):
        result = self.top.call.groupAndServices(groupingKey='ip', key='value')
        self.assertEqual(1, len(result))
        group, services = result[0]
        self.assertEqual('IP: 1.2.3.4', group)
        self.assertEqual(['id4', 'id5', 'id1', 'id2', 'id3'], [s.identifier for s in services])
        self.assertEqual(['listServices'], self.observer.calledMethodNames())
        self.assertEqual({'key': 'value'}, self.observer.calledMethods[0].kwargs)

    def testListGroupings(self):
        self.assertEqual([
            ('default', 'Default'),
            ('error', 'Error'),
            ('ip', 'IP-Address'),
            ('rw', 'On/Off'),
            ('version', 'Version')], self.top.call.listGroupings())


    #hellpers
    def addService(self, identifier, number, type):
        s = Service(identifier=identifier, type=type, lastseen=time(), ipAddress='1.2.3.4', number=number, infoport=1234)
        self.services[identifier] = s
        return s