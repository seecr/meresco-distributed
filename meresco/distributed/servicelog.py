## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2014-2017 Seecr (Seek You Too B.V.) http://seecr.nl
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

from os import listdir, stat
from os.path import join, basename, isfile
from string import atol
from time import strftime, localtime

from meresco.core import Observable


class ServiceLog(Observable):
    def __init__(self, identifier, serviceDir='/etc/service', **kwargs):
        Observable.__init__(self, **kwargs)
        self._identifier = identifier
        self._serviceDir = serviceDir

    def getLogFiles(self):
        servicedirs =[join(self._serviceDir, d) for d in listdir(self._serviceDir) if self._identifier in d]
        result = []
        for d in sorted(servicedirs):
            serviceName = basename(d)
            logDir = join(d, 'log', 'main')
            files = [(serviceName, f, formatStamp(stat(join(logDir, f)).st_mtime)) for f in listdir(logDir) if f.endswith('.s') or f.endswith('.u') or f == 'current']
            result.extend(reversed(sorted(files)))
        return result

    def getLogLines(self, dirname, filename, filterValue=None, filterStamp=None):
        filepath = join(self._serviceDir, dirname, 'log', 'main', filename)
        if not isfile(filepath):
            yield 'Log not found'
            return
        for line in open(filepath):
            if filterValue and filterValue not in line:
                continue
            time, value = stampedLine(line)
            if not filterStamp or filterStamp in time:
                yield time, value


def formatStamp(stamp):
    return strftime("%Y-%m-%d %H:%M:%S", localtime(stamp))

def stampedLine(line):
    stamp, value = line.split(' ', 1)
    time = tai64ToTime(stamp)
    return time, value

def tai64ToTime(stamp):
    secs = long(atol(stamp[1:17], 16))
    nsec = long(atol(stamp[17:25], 16))
    return "%s.%03d" % (strftime("%Y-%m-%d %H:%M:%S", localtime(int(secs - EPOCH))), nsec/10**6)

EPOCH = 4611686018427387914L
