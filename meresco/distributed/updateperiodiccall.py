## begin license ##
#
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  a project of the Koninklijke Bibliotheek
#  and provides a search service for all public
#  libraries in the Netherlands.
#
# Copyright (C) 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from meresco.core import Observable

from meresco.components import Schedule


class UpdatePeriodicCall(Observable):
    def __init__(self, scheduleConfigKey, default=None, name=None):
        Observable.__init__(self, name)
        self._scheduleConfigKey = scheduleConfigKey
        self._default = default

    def updateConfig(self, config, **kwargs):
        state = self.call.getState()
        scheduleConfig = config.get(self._scheduleConfigKey, self._default)
        if scheduleConfig is None:
            if not state.paused:
                self.call.pause()
            return
        newSchedule = Schedule(**scheduleConfig)
        if state.schedule != newSchedule:
            self.call.setSchedule(schedule=newSchedule)
            if state.paused:
                self.call.resume()
        return
        yield
