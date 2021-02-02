## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015 Stichting Kennisnet http://www.kennisnet.nl
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
from meresco.distributed.servicestate import ServiceState

class ServiceStateTest(SeecrTestCase):
    def testZeroErrors(self):
        state = ServiceState(lambda: [downloadState(error=False)])
        dataDict = {}
        state.serviceData(dataDict)
        self.assertEqual({}, dataDict)

    def testOneError(self):
        state = ServiceState([downloadState(error=True)])
        dataDict = {}
        state.serviceData(dataDict)
        self.assertEqual({'errors': 1}, dataDict)

    def testTwoErrors(self):
        state = ServiceState([downloadState(True), downloadState(False), downloadState(True)])
        dataDict = {}
        state.serviceData(dataDict)
        self.assertEqual({'errors': 2}, dataDict)

    def testWarnings(self):
        state = ServiceState.asWarning([downloadState(True)])
        dataDict = {}
        state.serviceData(dataDict)
        self.assertEqual({'warnings': 1}, dataDict)

def downloadState(error=True):
    downloadProcessorState = CallTrace('downloadProcessorState')
    downloadProcessorState.errorState = error
    return downloadProcessorState
