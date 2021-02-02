## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
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
from meresco.distributed import ServiceManagement
from weightless.core import consume

class ServiceManagementTest(SeecrTestCase):

    def testMakeUpdateIps(self):
        component = CallTrace()
        updateIps = ServiceManagement(reactor=None, admin=('host', 1234), configDownloadProcessor=CallTrace(), identifier=None, serviceType=None, statePath=None, version='1.0').makeUpdateIps(configSelector=lambda config: config['ips'], component=component)
        consume(updateIps.updateConfig(config={'ips':[
                { 'ip': '1.1.1.1' },
                { 'start': '2.2.2.1', 'end': '2.2.2.3'},
            ]}))
        self.assertEqual(["updateIps"], component.calledMethodNames())
        updateIpsKwargs = component.calledMethods[0].kwargs
        self.assertEqual(set(['ipAddresses', 'ipRanges']), set(updateIpsKwargs))
        self.assertEqual(set([('2.2.2.1', '2.2.2.3')]), updateIpsKwargs['ipRanges'])
        ipAddresses = updateIpsKwargs['ipAddresses']
        self.assertTrue('127.0.0.1' in ipAddresses)
        self.assertTrue('1.1.1.1' in ipAddresses)
