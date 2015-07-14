## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from meresco.core import Observable
from meresco.distributed.constants import WRITABLE, READABLE

from meresco.components import Schedule

from .constants import OAI_DOWNLOAD_INTERVAL, OAI_DOWNLOAD_PERIOD_CONFIG_KEY


class UpdatePeriodicDownload(Observable):
    def __init__(self, serviceIdentifier, periodicDownloadName, sourceServiceType, sourceServiceIdentifier=None, pollIntervalConfigSelector=None, name=None, **kwargs):
        Observable.__init__(self, name)
        self._serviceIdentifier = serviceIdentifier
        self._periodicDownloadName = periodicDownloadName
        self._pollIntervalConfigSelector = pollIntervalConfigSelector or oaiDownloadConfigSelector
        self._sourceServiceType = sourceServiceType
        self._sourceServiceIdentifier = sourceServiceIdentifier
        self._extraKwargs = kwargs

    def updateConfig(self, config, services, **kwargs):
        state = self.call.getState()
        pollInterval = float(self._pollIntervalConfigSelector(config))
        if state.schedule.period != pollInterval:
            self.call.setSchedule(schedule=Schedule(period=pollInterval))
        try:
            host, port = self.call.selectHostPortForService(type=self._sourceServiceType, flag=READABLE, remember=self._sourceServiceIdentifier is None, identifier=self._sourceServiceIdentifier, **self._extraKwargs)
        except ValueError:
            host, port = None, None
        if state.host != host or state.port != port:
            self.call.setDownloadAddress(host=host, port=port)
        serviceDict = services.get(self._serviceIdentifier, {})
        periodicDownloadPaused = config.get("%s.periodicDownload.%s.paused" % (self._serviceIdentifier, self._periodicDownloadName), False)
        paused = not state.host or not state.port or not WRITABLE.isSet(serviceDict) or periodicDownloadPaused
        if paused != state.paused:
            if paused:
                self.call.pause()
            else:
                self.call.resume()
        return
        yield


def oaiDownloadConfigSelector(config):
    return config.get(OAI_DOWNLOAD_PERIOD_CONFIG_KEY, OAI_DOWNLOAD_INTERVAL)
