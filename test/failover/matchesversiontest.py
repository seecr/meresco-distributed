## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2018 Seecr (Seek You Too B.V.) http://seecr.nl
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

from weightless.core import be, asString, consume, NoneOfTheObserversRespond, retval
from meresco.core import Observable
from meresco.distributed.failover import MatchesVersion


class MatchesVersionTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.matchesVersion = MatchesVersion(minVersion='1', untilVersion='3')
        self.observer = CallTrace('observer', methods=dict(somemessage=lambda: (x for x in ['result'])))
        self.top = be((Observable(),
            (self.matchesVersion,
                (self.observer,)
            )
        ))

    def testDoesNotMatchNoConfig(self):
        self.assertEqual('', asString(self.top.all.somemessage()))
        self.assertEqual([], self.observer.calledMethodNames())

    def testDoesNotMatchNoVersion(self):
        consume(self.matchesVersion.updateConfig(config={'foo': 'bar'}))
        self.assertEqual('', asString(self.top.all.somemessage()))
        self.assertEqual([], self.observer.calledMethodNames())

    def testDoesNotMatch(self):
        consume(self.matchesVersion.updateConfig(config={'softwareVersion': '0.1'}))
        self.assertEqual('', asString(self.top.all.somemessage()))
        self.assertEqual([], self.observer.calledMethodNames())

    def testDoesMatch(self):
        consume(self.matchesVersion.updateConfig(config={'softwareVersion': '2'}))
        self.assertEqual('result', asString(self.top.all.somemessage()))
        self.assertEqual(['somemessage'], self.observer.calledMethodNames())


    # MatchesVersion is expected to be invoked with 'all', but testing for 'do', 'call' and 'any' invocation just in case

    def testDoesNotMatchDo(self):
        consume(self.matchesVersion.updateConfig(config={'softwareVersion': '0.1'}))
        self.top.do.somemessage()
        self.assertEqual([], self.observer.calledMethodNames())

    def testDoesMatchDo(self):
        consume(self.matchesVersion.updateConfig(config={'softwareVersion': '2'}))
        self.top.do.anothermessage()
        self.assertEqual(['anothermessage'], self.observer.calledMethodNames())

    def testDoesNotMatchCall(self):
        consume(self.matchesVersion.updateConfig(config={'softwareVersion': '0.1'}))
        try:
            _ = self.top.call.somemessage()
            self.fail()
        except NoneOfTheObserversRespond:
            pass
        self.assertEqual([], self.observer.calledMethodNames())

    def testDoesMatchCall(self):
        consume(self.matchesVersion.updateConfig(config={'softwareVersion': '2'}))
        _ = self.top.call.somemessage()
        self.assertEqual(['somemessage'], self.observer.calledMethodNames())

    def testDoesNotMatchAny(self):
        consume(self.matchesVersion.updateConfig(config={'softwareVersion': '0.1'}))
        try:
            _ = retval(self.top.any.somemessage())
            self.fail()
        except NoneOfTheObserversRespond:
            pass
        self.assertEqual([], self.observer.calledMethodNames())

    def testDoesMatchAny(self):
        consume(self.matchesVersion.updateConfig(config={'softwareVersion': '2'}))
        _ = retval(self.top.any.somemessage())
        self.assertEqual(['somemessage'], self.observer.calledMethodNames())
