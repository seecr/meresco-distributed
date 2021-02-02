## begin license ##
#
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  a project of the Koninklijke Bibliotheek
#  and provides a search service for all public
#  libraries in the Netherlands.
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
#
# This file is part of "NBC+ (Zoekplatform BNL)"
#
# "NBC+ (Zoekplatform BNL)" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "NBC+ (Zoekplatform BNL)" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "NBC+ (Zoekplatform BNL)"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from os import remove
from os.path import isfile, join
from time import time

from meresco.distributed.servicestate import ERROR

from seecr.zulutime import ZuluTime
from seecr.utils import readFromFile, atomic_write


class CrashDetect(object):
    def __init__(self, stateDir, severity=ERROR):
        self._filePath = join(stateDir, 'lastSafePoint')
        self._severity = severity
        self.didCrash = isfile(self._filePath)
        self._markSafePoint()

    def serviceData(self, dataDict):
        if self.didCrash:
            errors = dataDict.get(self._severity, 0)
            dataDict[self._severity] = errors + 1

    def errorMessage(self):
        return 'Data considered incomplete after crash [last safe point: %s].' % ZuluTime.parseEpoch(self.lastSafePoint()).zulu() if self.didCrash else None

    def commit(self):
        self._markSafePoint()

    def handleShutdown(self):
        if not self.didCrash:
            remove(self._filePath)

    def lastSafePoint(self):
        return float(readFromFile(self._filePath))

    def _markSafePoint(self):
        if not self.didCrash:
            with atomic_write(self._filePath) as f:
                f.write("%f" % self._time())

    def _time(self):
        return time()
