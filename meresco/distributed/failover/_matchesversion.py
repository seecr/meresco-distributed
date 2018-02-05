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

from weightless.core import NoneOfTheObserversRespond, DeclineMessage
from meresco.core import Observable


class MatchesVersion(Observable):
    def __init__(self, minVersion, untilVersion, **kwargs):
        Observable.__init__(self, **kwargs)
        self._minVersion = minVersion
        self._untilVersion = untilVersion
        self._actualVersion = None

    def updateConfig(self, config, **kwargs):
        yield self.all.updateConfig(config=config, **kwargs)
        self._actualVersion = config.get('software_version')

    def all_unknown(self, message, *args, **kwargs):
        if self._matches():
            yield self.all.unknown(message, *args, **kwargs)

    def any_unknown(self, message, *args, **kwargs):
        if self._matches():
            try:
                response = yield self.any.unknown(message, *args, **kwargs)
                raise StopIteration(response)
            except NoneOfTheObserversRespond:
                pass
        raise DeclineMessage

    def do_unknown(self, message, *args, **kwargs):
        if self._matches():
            self.do.unknown(message, *args, **kwargs)

    def call_unknown(self, message, *args, **kwargs):
        if self._matches():
            try:
                return self.call.unknown(message, *args, **kwargs)
            except NoneOfTheObserversRespond:
                pass
        raise DeclineMessage

    def _matches(self):
        return self._minVersion <= self._actualVersion < self._untilVersion
