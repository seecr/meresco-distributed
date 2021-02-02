## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2016, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015, 2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2021 SURF https://www.surf.nl
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
from os.path import join, isdir
from uuid import uuid4

from meresco.components.version import Version
from weightless.core import consume
from meresco.distributed import Service, SelectService, ServiceRegistry
from meresco.distributed.constants import READABLE, READWRITE
from time import time

VERSION = "42.0"
class SelectServiceTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.selectService = SelectService(
            currentVersion=VERSION,
            statePath=join(self.tempdir, 'state'),
        )

    def testShouldCreateStatePathIfNecessary(self):
        self.assertTrue(isdir(join(self.tempdir, 'state')))

    def testShouldSelectRequestedServiceType(self):
        consume(self.selectService.updateConfig(
            config={},
            services={
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.4', 'infoport':2000, 'readable': True, 'data':{'VERSION': VERSION}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'other', 'ipAddress': '4.3.2.1', 'infoport':2002, 'readable': True, 'data':{'VERSION': VERSION}},
            },
        ))
        host, port = self.selectService.selectHostPortForService(type='plein', flag=READABLE)
        self.assertEqual('1.2.3.4', host)
        self.assertEqual(2000, port)

    def testShouldSelectRequestedServiceTypeAndMatchingVersion(self):
        consume(self.selectService.updateConfig(
            config={},
            services={
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.4', 'infoport':2000, 'readable': True, 'data':{'VERSION': '0.9.3.7'}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport':2001, 'readable': True, 'data':{'VERSION': '0.10.37'}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'other', 'ipAddress': '4.3.2.1', 'infoport':2002, 'readable': True, 'data':{'VERSION': '0.10.42'}},
            },
        ))
        for i in range(50):
            host, port = self.selectService.selectHostPortForService(type='plein', flag=READABLE, minVersion='0.10', untilVersion='0.11')
            self.assertEqual('1.2.3.5', host)
            self.assertEqual(2001, port)

    def testHostsAndPortsforServiceWithVersion(self):
        consume(self.selectService.updateConfig(
            config={},
            services={
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'index', 'ipAddress': '1.2.3.4', 'infoport':2000, 'readable': True, 'data':{'VERSION': '0.9.3.7'}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'index', 'ipAddress': '1.2.3.5', 'infoport':2001, 'readable': True, 'data':{'VERSION': '0.10.37'}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'index', 'ipAddress': '1.2.3.6', 'infoport':2002, 'readable': True, 'data':{'VERSION': '0.10.42'}},
            },
        ))
        result = set(self.selectService.hostsAndPortsForService(type='index', flag=READABLE, minVersion='0.10', untilVersion='0.11'))
        self.assertEqual(set([('1.2.3.5', 2001),('1.2.3.6', 2002)]), result)

    def testShouldSelectDefaultMajorVersion(self):
        currentVersion = VERSION
        currentMajor = Version(currentVersion).majorVersion()         # 1.2 (assuming VERSION = 1.2.x)
        currentLesserVersion = str(currentMajor) + '.1'               # 1.2.1
        nextVersion = str(currentMajor.nextMajorVersion()) + '.3'     # 1.3.3
        aPreviousMajorVersion = '1.1.4.5'
        consume(self.selectService.updateConfig(
            config={},
            services={
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.4', 'infoport':2000, 'readable': True, 'data':{'VERSION': aPreviousMajorVersion}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport':2001, 'readable': True, 'data':{'VERSION': currentLesserVersion}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.6', 'infoport':2001, 'readable': True, 'data':{'VERSION': nextVersion}},
            },
        ))
        for i in range(50):
            # Select default major version
            host, port = self.selectService.selectHostPortForService(type='plein', flag=READABLE, minVersion=None, untilVersion=None)
            self.assertEqual('1.2.3.5', host)
            self.assertEqual(2001, port)
        # automatically untilVersion is minorVersion.nextMajorVersion()
        for i in range(50):
            host, port = self.selectService.selectHostPortForService(type='plein', flag=READABLE, minVersion=currentLesserVersion, untilVersion=None)
            self.assertEqual('1.2.3.5', host)
            self.assertEqual(2001, port)
        currentHigherVersion = str(currentMajor) + '.3'
        self.assertRaises(ValueError, lambda: self.selectService.selectHostPortForService(type='plein', flag=READABLE, minVersion=currentHigherVersion, untilVersion=None))

    def testSelectWithUntilVersion(self):
        self.selectService = SelectService(
            currentVersion='4.5',
            statePath=join(self.tempdir, 'state'),
            untilVersion='25.3',
        )
        consume(self.selectService.updateConfig(
            config={},
            services={
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.4', 'infoport':2000, 'readable': True, 'data':{'VERSION': '1.0'}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport':2001, 'readable': True, 'data':{'VERSION': '24.5'}},
            },
        ))
        host, port = self.selectService.selectHostPortForService(type='plein', flag=READABLE)
        self.assertEqual(2001, port)

    def testShouldRaiseValueErrorIfServiceNotAvailable(self):
        consume(self.selectService.updateConfig(
            config={},
            services={
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'other', 'ipAddress': '4.3.2.1', 'infoport':2000},
            },
        ))
        self.assertRaises(ValueError, self.selectService.selectHostPortForService, type='plein', flag=READABLE)

    def testShouldSelectHostPortForService(self):
        consume(self.selectService.updateConfig(
            config={},
            services={
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.4', 'infoport': 4, 'readable': True, 'data':{'VERSION': VERSION}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport': 5, 'readable': True, 'data':{'VERSION': VERSION}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'other', 'ipAddress': '4.3.2.1', 'infoport': 2000, 'readable': True, 'data':{'VERSION': VERSION}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '4.3.2.2', 'infoport': 2001, 'readable': False, 'data':{'VERSION': VERSION}},
            },
        ))
        selectedHostPort = set()
        for i in range(20):
            result = self.selectService.selectHostPortForService(type='plein', flag=READABLE)
            selectedHostPort.add(result)
        self.assertEqual(set([('1.2.3.4', 4), ('1.2.3.5', 5)]), selectedHostPort)

    def testShouldSelectHostsAndPortsForService(self):
        consume(self.selectService.updateConfig(
            config={},
            services={
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.4', 'infoport': 4, 'readable': True, 'data':{'VERSION': VERSION}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport': 5, 'readable': True, 'data':{'VERSION': VERSION}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'other', 'ipAddress': '4.3.2.1', 'infoport': 2000, 'readable': True, 'data':{'VERSION': VERSION}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '4.3.2.2', 'infoport': 2001, 'readable': False, 'data':{'VERSION': VERSION}},
            },
        ))
        selectedHostPort = self.selectService.hostsAndPortsForService(type='plein', flag=READABLE)
        self.assertEqual(set([('1.2.3.4', 4), ('1.2.3.5', 5)]), set(selectedHostPort))

    def testShouldSelectHostPortForSpecificEndpoint(self):
        consume(self.selectService.updateConfig(
            config={},
            services={
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'kennisbank', 'ipAddress': '1.2.3.4', 'infoport': 4, 'data': {'endpoints': {'triplestore': 'http://1.3.5.7:8000/sparql'}, 'VERSION': VERSION}, 'readable': True},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport': 5, 'readable': True, 'data':{'VERSION': VERSION}},
            },
        ))
        selectedHostPort = set()
        for i in range(20):
            result = self.selectService.selectHostPortForService(type='kennisbank', flag=READABLE, endpoint='triplestore')
            selectedHostPort.add(result)
        self.assertEqual(set([('1.3.5.7', 8000)]), selectedHostPort)

    def testShouldRaiseValueErrorIfRequestedEndpointNotAvailable(self):
        consume(self.selectService.updateConfig(
            config={},
            services={
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'kennisbank', 'ipAddress': '1.2.3.4', 'infoport': 4, 'data': {'endpoints': {'ignored': 'http://1.3.5.7:8000/sparql'}, 'VERSION': VERSION}, 'readable': True},
            },
        ))
        try:
            result = self.selectService.selectHostPortForService(type='kennisbank', flag=READABLE, endpoint='triplestore')
            print(result)
            self.fail()
        except ValueError as e:
            self.assertTrue(str(e).startswith("No endpoint 'triplestore' found for service 'kennisbank' with identifier '"), str(e))

    def testShouldSelectRememberedService(self):
        consume(self.selectService.updateConfig(
            config={},
            services={
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.4', 'infoport':2000, 'readable': True, 'data':{'VERSION': VERSION}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport':2001, 'readable': True, 'data':{'VERSION': VERSION}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'other', 'ipAddress': '4.3.2.1', 'infoport':2002, 'readable': True, 'data':{'VERSION': VERSION}},
            },
        ))
        host, port = self.selectService.selectHostPortForService(type='plein', flag=READABLE, remember=True)
        selectedHostPort = set()
        for i in range(10):
            result = self.selectService.selectHostPortForService(type='plein', flag=READABLE, remember=True)
            selectedHostPort.add(result)
        self.assertEqual(set([(host, port)]), selectedHostPort)

    def testShouldRaiseValueErrorIfRememberedServiceWrongVersion(self):
        serviceIdentifier = str(uuid4())
        consume(self.selectService.updateConfig(
            config={},
            services={
                serviceIdentifier: {'identifier': serviceIdentifier, 'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport': 2000, 'readable': True, 'data':{'VERSION': VERSION}},
            },
        ))
        self.selectService.selectHostPortForService(type='plein', flag=READABLE, remember=True)
        consume(self.selectService.updateConfig(
            config={},
            services={
                serviceIdentifier: {'identifier': serviceIdentifier, 'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport': 2000, 'readable': True, 'data':{'VERSION': '0.9'}},
            },
        ))
        self.assertRaises(ValueError, self.selectService.selectHostPortForService, type='plein', flag=READABLE, remember=True)
        result = self.selectService.selectHostPortForService(type='plein', flag=READABLE, remember=True, minVersion='0.9')
        self.assertEqual(('1.2.3.5', 2000), result)

    def testSetChosenService(self):
        serviceIdentifier = str(uuid4())
        consume(self.selectService.updateConfig(
            config={},
            services={
                serviceIdentifier: {'identifier': serviceIdentifier, 'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport': 2000, 'readable': True, 'data':{'VERSION': VERSION}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.6', 'infoport': 2001, 'readable': True, 'data':{'VERSION': VERSION}},
            },
        ))
        self.selectService.setRequestedServiceIdentifier(identifier=serviceIdentifier, type='plein')
        selectedHostPort = set()
        for i in range(10):
            result = self.selectService.selectHostPortForService(type='plein', flag=READABLE, remember=True)
            selectedHostPort.add(result)
        self.assertEqual(set([('1.2.3.5', 2000)]), selectedHostPort)

    def testShouldRaiseValueErrorIfRememberedServiceWithIdentifierNotAvailable(self):
        serviceIdentifier = str(uuid4())
        consume(self.selectService.updateConfig(
            config={},
            services={
                serviceIdentifier: {'identifier': serviceIdentifier, 'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport': 2000, 'readable': True, 'data':{'VERSION': VERSION}},
            },
        ))
        self.selectService.selectHostPortForService(type='plein', flag=READABLE, remember=True)
        consume(self.selectService.updateConfig(
            config={},
            services={
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport': 2000, 'readable': True, 'data':{'VERSION': VERSION}},
            },
        ))
        self.assertRaises(ValueError, self.selectService.selectHostPortForService, type='plein', flag=READABLE, remember=True)

        consume(self.selectService.updateConfig(
            config={},
            services={
                serviceIdentifier: {'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport': 2000, 'readable': False, 'data':{'VERSION': VERSION}},
            },
        ))
        self.assertRaises(ValueError, self.selectService.selectHostPortForService, type='plein', flag=READABLE, remember=True)

    def testForAdmin(self):
        def newService(port, readable):
            return Service(identifier=str(uuid4()),
                    type='type',
                    ipAddress='10.10.10.10',
                    infoport=port,
                    readable=readable,
                    data={'VERSION': VERSION}
                )
        services = [newService(1, False), newService(2, True)]
        serviceRegistry = CallTrace('registry')
        serviceRegistry.returnValues['iterServices'] = services
        selectService = SelectService.forAdmin(serviceRegistry, currentVersion=VERSION)
        hostsAndPorts = list(selectService.hostsAndPortsForService(type='type', flag=READABLE))
        self.assertEqual([2], [port for h, port in hostsAndPorts])

    def testSelectHostPortForGivenIdentifier(self):
        serviceIdentifier = str(uuid4())
        consume(self.selectService.updateConfig(
            config={},
            services={
                serviceIdentifier: {'identifier': serviceIdentifier, 'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport': 2000, 'readable': True, 'data':{'VERSION': VERSION}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.6', 'infoport': 2001, 'readable': True, 'data':{'VERSION': VERSION}},
            },
        ))
        selectedHostPort = set()
        for i in range(10):
            result = self.selectService.selectHostPortForService(identifier=serviceIdentifier, type='plein', flag=READABLE, remember=True)
            selectedHostPort.add(result)
        self.assertEqual(set([('1.2.3.5', 2000)]), selectedHostPort)

    def testRequestTwiceFromCache(self):
        serviceIdentifier = str(uuid4())
        consume(self.selectService.updateConfig(
            config={},
            services={
                serviceIdentifier: {'identifier': serviceIdentifier, 'type': 'plein', 'ipAddress': '1.2.3.5', 'infoport': 2000, 'readable': True, 'data':{'VERSION': VERSION}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.6', 'infoport': 2001, 'readable': True, 'data':{'VERSION': VERSION}},
            },
        ))
        selectedHostPort = set()
        t0 = time()
        for i in range(1000):
            result = self.selectService.selectHostPortForService(type='plein', flag=READABLE)
            selectedHostPort.add(result)
        t1 = time()
        self.assertTrue(t1 - t0 < 0.011, t1 - t0)
        self.assertEqual(set([('1.2.3.5', 2000), ('1.2.3.6', 2001)]), selectedHostPort)

    def testNoCacheForAdmin(self):
        serviceRegistry = ServiceRegistry(reactor=None, stateDir=self.tempdir, domainname='example.org')
        selectService = SelectService.forAdmin(serviceRegistry, currentVersion=VERSION, statePath=join(self.tempdir, 'state'))
        serviceIdentifier = str(uuid4())
        serviceRegistry.updateService(identifier=serviceIdentifier, type='plein', ipAddress='1.2.3.5', infoport=2000, data={'VERSION': VERSION})
        serviceRegistry.setFlag(identifier=serviceIdentifier, flag=READABLE, value=True, immediate=True)
        result = selectService.selectHostPortForService(type='plein', flag=READABLE)
        self.assertEqual(('1.2.3.5', 2000), result)

        serviceRegistry.updateService(identifier=serviceIdentifier, type='plein', ipAddress='1.2.3.5', infoport=2001, data={'VERSION': VERSION})
        result = selectService.selectHostPortForService(type='plein', flag=READABLE)
        self.assertEqual(('1.2.3.5', 2001), result)

    def testSelectWithBothReadableAndWritableFlag(self):
        self.selectService = SelectService(
            currentVersion='4.5',
            statePath=join(self.tempdir, 'state'),
        )
        consume(self.selectService.updateConfig(
            config={},
            services={
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.4', 'infoport':2000, 'readable': False, 'writable': True, 'data':{'VERSION': '4.5'}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.4', 'infoport':2001, 'readable': True, 'writable': False, 'data':{'VERSION': '4.5'}},
                str(uuid4()): {'identifier': str(uuid4()), 'type': 'plein', 'ipAddress': '1.2.3.4', 'infoport':2002, 'readable': True, 'writable': True, 'data':{'VERSION': '4.5'}},
            },
        ))
        host, port = self.selectService.selectHostPortForService(type='plein', flag=READWRITE)
        self.assertEqual(2002, port)
