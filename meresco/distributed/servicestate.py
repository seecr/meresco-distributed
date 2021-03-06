## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2014-2016 Seecr (Seek You Too B.V.) http://seecr.nl
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

WARNING = 'warnings'
ERROR = 'errors'

class ServiceState(object):
    def __init__(self, states, type=ERROR):
        self._states = states if hasattr(states, '__call__') else (lambda: states)
        self._type = type

    def serviceData(self, dataDict):
        errors = 0
        for state in self._states():
            if state.errorState:
                errors += 1
        if errors:
            dataDict[self._type] = errors

    @classmethod
    def asWarning(cls, states):
        return cls(states, type=WARNING)


class ServiceErrorState(object):
    def serviceData(self, dataDict):
        dataDict["errors"] = 1
