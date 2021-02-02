## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2014-2016, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from weightless.core import consume
from meresco.components import Schedule

from meresco.distributed.updateperiodiccall import UpdatePeriodicCall


class UpdatePeriodicCallTest(SeecrTestCase):
    def testUpdateSchedule(self):
        class MockState():
            paused = True
            schedule = None
        observer = CallTrace(returnValues=dict(getState=MockState()))
        upc = UpdatePeriodicCall(scheduleConfigKey='akey')
        upc.addObserver(observer)
        consume(upc.updateConfig(config={'akey': {'period': 1}}, services={}))
        self.assertEqual(['getState', 'setSchedule', 'resume'], observer.calledMethodNames())
        self.assertEqual(Schedule(period=1), observer.calledMethods[1].kwargs['schedule'])

    def testUpdateScheduleAlreadyRunning(self):
        class MockState():
            paused = False
            schedule = Schedule(period=2)
        observer = CallTrace(returnValues=dict(getState=MockState()))
        upc = UpdatePeriodicCall(scheduleConfigKey='akey')
        upc.addObserver(observer)
        consume(upc.updateConfig(config={'akey': {'period': 1}}, services={}))
        self.assertEqual(['getState', 'setSchedule'], observer.calledMethodNames())
        self.assertEqual(Schedule(period=1), observer.calledMethods[1].kwargs['schedule'])

    def testKeyNotInConfigSetsDefault(self):
        class MockState():
            paused = False
            schedule = Schedule(period=2)
        observer = CallTrace(returnValues=dict(getState=MockState()))
        upc = UpdatePeriodicCall(scheduleConfigKey='akey', default=dict(period=3))
        upc.addObserver(observer)
        consume(upc.updateConfig(config={}, services={}))
        self.assertEqual(['getState', 'setSchedule'], observer.calledMethodNames())
        self.assertEqual(Schedule(period=3), observer.calledMethods[1].kwargs['schedule'])

    def testKeyNotInConfigWillPauseIfNoDefault(self):
        class MockState():
            paused = False
            schedule = Schedule(period=2)
        observer = CallTrace(returnValues=dict(getState=MockState()))
        upc = UpdatePeriodicCall(scheduleConfigKey='akey')
        upc.addObserver(observer)
        consume(upc.updateConfig(config={}, services={}))
        self.assertEqual(['getState', 'pause'], observer.calledMethodNames())

    def testKeyNotInConfigDoesNothingIfAlreadyPaused(self):
        class MockState():
            paused = True
            schedule = None
        observer = CallTrace(returnValues=dict(getState=MockState()))
        upc = UpdatePeriodicCall(scheduleConfigKey='akey')
        upc.addObserver(observer)
        consume(upc.updateConfig(config={}, services={}))
        self.assertEqual(['getState'], observer.calledMethodNames())

    def testDontUpdateScheduleIfNotChanged(self):
        class MockState():
            paused = False
            schedule = Schedule(period=2)
        observer = CallTrace(returnValues=dict(getState=MockState()))
        upc = UpdatePeriodicCall(scheduleConfigKey='akey')
        upc.addObserver(observer)
        consume(upc.updateConfig(config={'akey': {'period': 2}}, services={}))
        self.assertEqual(['getState'], observer.calledMethodNames())

    def testPeriodConfigKey(self):
        class MockState():
            paused = True
            schedule = None
        observer = CallTrace(returnValues=dict(getState=MockState()))
        upc = UpdatePeriodicCall(periodConfigKey='akey')
        upc.addObserver(observer)
        consume(upc.updateConfig(config={'akey': 1}, services={}))
        self.assertEqual(['getState', 'setSchedule', 'resume'], observer.calledMethodNames())
        self.assertEqual(Schedule(period=1), observer.calledMethods[1].kwargs['schedule'])

    def testBothScheduleAndPeriodNotAllowed(self):
        self.assertRaises(ValueError, lambda: UpdatePeriodicCall(periodConfigKey='akey', scheduleConfigKey='otherkey'))

