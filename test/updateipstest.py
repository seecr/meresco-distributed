## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2014-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from weightless.core import consume, be

from meresco.core import Observable

from meresco.distributed import UpdateIps


class UpdateIpsTest(SeecrTestCase):
    def createTree(self, **kwargs):
        self.updateIps = UpdateIps(**kwargs)
        self.observer = CallTrace('Observer')
        self.top = be((Observable(),
            (self.updateIps,
                (self.observer,),
            )
        ))
    def testDataExtractedFromConfig(self):
        cs = lambda c: c.get('key_a', []) + c.get('key_b', [])
        self.createTree(configSelector=cs)

        consume(self.top.all.updateConfig(config=CONFIG_EXAMPLE, services={}))
        self.assertEqual(1, len(self.observer.calledMethods))

        updateIps, = self.observer.calledMethods
        self.assertEqual(tuple(), updateIps.args)

        # return-type is a set i.s.o. a list, but works equally well with IpFilter / Deproxy.
        self.assertEqual(dict(
                ipAddresses=set(['1.2.3.5', '1.2.3.4', '127.0.0.1']),
                ipRanges=set([('0.0.0.0', '10.10.10.10'), ('20.20.20.20', '40.40.40.40'), '10.10.10.0/24']),
            ), updateIps.kwargs)

    def testStaticIpAddresses(self):
        emptyCs = lambda c: []
        self.createTree(configSelector=emptyCs, staticIpAddresses=['0.9.1.1'], includeLocalhost=False)

        consume(self.top.all.updateConfig(config=CONFIG_EXAMPLE, services={}))
        self.assertEqual(1, len(self.observer.calledMethods))

        updateIps, = self.observer.calledMethods
        self.assertEqual(tuple(), updateIps.args)

        # return-type is a set i.s.o. a list, but works equally well with IpFilter / Deproxy.
        self.assertEqual(dict(
                ipAddresses=set(['0.9.1.1']),
                ipRanges=set([]),
            ), updateIps.kwargs)

    def testIncludeLocalhost(self):
        # ... is False
        emptyCs = lambda c: []
        self.createTree(configSelector=emptyCs, includeLocalhost=False)
        consume(self.top.all.updateConfig(config={}, services={}))
        self.assertEqual(1, len(self.observer.calledMethods))

        updateIps, = self.observer.calledMethods
        self.assertEqual(dict(
                ipAddresses=set([]),
                ipRanges=set([]),
            ), updateIps.kwargs)

        # ... is True
        emptyCs = lambda c: []
        self.createTree(configSelector=emptyCs, includeLocalhost=True)
        consume(self.top.all.updateConfig(config={}, services={}))
        self.assertEqual(1, len(self.observer.calledMethods))

        updateIps, = self.observer.calledMethods
        self.assertEqual(dict(
                ipAddresses=set(['127.0.0.1']),
                ipRanges=set([]),
            ), updateIps.kwargs)

    def testStaticIpAddressesWithIncludeLocalhost(self):
        emptyCs = lambda c: []
        self.createTree(configSelector=emptyCs, staticIpAddresses=['0.9.1.1'], includeLocalhost=True)

        consume(self.top.all.updateConfig(config={}, services={}))
        self.assertEqual(1, len(self.observer.calledMethods))

        updateIps, = self.observer.calledMethods
        self.assertEqual(tuple(), updateIps.args)

        # return-type is a set i.s.o. a list, but works equally well with IpFilter / Deproxy.
        self.assertEqual(dict(
                ipAddresses=set(['0.9.1.1', '127.0.0.1']),
                ipRanges=set([]),
            ), updateIps.kwargs)

    def testStaticIpAddressesMergedWithConfigResult(self):
        cs = lambda c: c.get('key_a', []) + c.get('key_b', [])
        self.createTree(configSelector=cs, staticIpAddresses=['0.9.1.1'])

        consume(self.top.all.updateConfig(config=CONFIG_EXAMPLE, services={}))
        self.assertEqual(1, len(self.observer.calledMethods))

        updateIps, = self.observer.calledMethods
        self.assertEqual(tuple(), updateIps.args)

        # return-type is a set i.s.o. a list, but works equally well with IpFilter / Deproxy.
        self.assertEqual(dict(
                ipAddresses=set(['0.9.1.1', '1.2.3.5', '1.2.3.4', '127.0.0.1']),
                ipRanges=set([('0.0.0.0', '10.10.10.10'), ('20.20.20.20', '40.40.40.40'), '10.10.10.0/24']),
            ), updateIps.kwargs)

CONFIG_EXAMPLE = {
    "key_a": [
        {
            "comment": 'will be ignored',
            "ip": '1.2.3.4',
        },
        {
            "comment": "a range",
            "start": '0.0.0.0',
            "end": '10.10.10.10'
        },
        {
            "comment": "a range",
            "start": '20.20.20.20',
            "end": '40.40.40.40'
        },
        {
            'comment': 'real range',
            'range': '10.10.10.0/24'
        },],
    "key_b": [
        {
            "comment": "Same range, different key",
            "start": '0.0.0.0',
            "end": '10.10.10.10'
        },
        {
            "comment": 'Same IP',
            "ip": '1.2.3.4',
        },
        {
            "comment": 'Other IP',
            "ip": '1.2.3.5',
        },],
    "key_ignored": [
        {
            "comment": "Ignored Range",
            "start": '11.11.11.11',
            "end": '21.21.21.21'
        },
        {
            "comment": 'Ignored IP',
            "ip": '99.99.99.99',
        }
    ],
}

