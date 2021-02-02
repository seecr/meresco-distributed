## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from os import remove
from os.path import isfile

from seecr.test import SeecrTestCase

from meresco.distributed.servicestate import WARNING
from meresco.distributed.crashdetect import CrashDetect


class CrashDetectTest(SeecrTestCase):
    def testNormalShutdown(self):
        cd = CrashDetect(self.tempdir)
        self.assertFalse(cd.didCrash)
        self.assertTrue(isfile(cd._filePath))
        cd.handleShutdown()
        self.assertFalse(isfile(cd._filePath))
        cd = CrashDetect(self.tempdir)
        self.assertFalse(cd.didCrash)
        dataDict = {}
        cd.serviceData(dataDict)
        self.assertEqual({}, dataDict)

    def testDidNotShutdownProperly(self):
        cd = CrashDetect(self.tempdir)
        cd = CrashDetect(self.tempdir) # reopen
        self.assertTrue(cd.didCrash)
        self.assertTrue(cd.errorMessage().startswith('Data considered incomplete after crash [last safe point: '), cd.errorMessage())
        dataDict = {}
        cd.serviceData(dataDict)
        self.assertEqual({'errors': 1}, dataDict)
        cd.handleShutdown()
        filePath = cd._filePath
        cd = None
        remove(filePath)  # manual reset
        cd = CrashDetect(self.tempdir)
        self.assertFalse(cd.didCrash)
        dataDict = {}
        cd.serviceData(dataDict)
        self.assertEqual({}, dataDict)

    def testShutdownAfterRestartAfterCrashKeepsErrorState(self):
        cd = CrashDetect(self.tempdir)
        cd = CrashDetect(self.tempdir) # reopen
        self.assertTrue(cd.didCrash)
        errorMessage = cd.errorMessage()
        self.assertTrue(errorMessage.startswith('Data considered incomplete after crash [last safe point: '), errorMessage)
        cd.handleShutdown()
        cd = CrashDetect(self.tempdir)
        self.assertTrue(cd.didCrash)
        self.assertEqual(errorMessage, cd.errorMessage())

    def testKeepEarliestCrashTimestamp(self):
        cd = CrashDetect(self.tempdir)
        lsc = cd.lastSafePoint()
        cd = CrashDetect(self.tempdir)
        self.assertTrue(cd.didCrash)
        self.assertEqual(lsc, cd.lastSafePoint())
        self.assertTrue(cd.errorMessage().startswith('Data considered incomplete after crash [last safe point: '), cd.errorMessage())
        cd = CrashDetect(self.tempdir)
        self.assertTrue(cd.didCrash)
        self.assertEqual(lsc, cd.lastSafePoint())

    def testServiceDataIncrement(self):
        dataDict = {'errors': 1}
        cd = CrashDetect(self.tempdir)
        cd = CrashDetect(self.tempdir)
        cd.serviceData(dataDict)
        self.assertEqual({'errors': 2}, dataDict)

    def testServiceDataWarningSeverity(self):
        dataDict = {'errors': 1}
        cd = CrashDetect(self.tempdir, severity=WARNING)
        cd = CrashDetect(self.tempdir, severity=WARNING)
        cd.serviceData(dataDict)
        self.assertEqual({'errors': 1, 'warnings': 1}, dataDict)
