## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from .selectservice import SelectService
from .servicelog import ServiceLog
from meresco.components import Schedule, PeriodicDownload
from meresco.components.json import JsonDict
from .constants import SERVICE_POLL_INTERVAL, ADMIN_DOWNLOAD_PERIOD_CONFIG_KEY
from weightless.core import be

class ServiceManagement(object):
    def __init__(self, reactor, admin, configDownloadProcessor, identifier, serviceType, statePath, version=None, documentationPath=None, enableSelectService=True):
        self._reactor = reactor
        self._adminHostname, self._adminPort = admin
        self.identifier = identifier
        self._serviceType = serviceType
        self._version = version
        self._selectService = SelectService(statePath=statePath, currentVersion=self._version) if enableSelectService else DummySelectService()
        self._latestConfiguration = JsonDict({})
        self._configDownloadProcessor = configDownloadProcessor
        self._documentationPath = documentationPath
        self._serviceLog = ServiceLog(identifier=identifier)
        self.createConfigUpdateTree()

    def updateConfig(self, config, **kwargs):
        yield self._selectService.updateConfig(config=config, **kwargs)
        self._configPeriodicDownload.setSchedule(
            Schedule(period=float(config.get(ADMIN_DOWNLOAD_PERIOD_CONFIG_KEY, SERVICE_POLL_INTERVAL)))
        )
        self._latestConfiguration = JsonDict(config=config, **kwargs)
        return

    def getServiceSelector(self):
        return self._selectService

    @property
    def gustosIdentifier(self):
        return "%s-%s" % (self._serviceType, self.identifier)

    def createConfigUpdateTree(self, configObservers=None):
        configObservers = configObservers or []
        if not getattr(self, '_configPeriodicDownload', None):
            self._configPeriodicDownload = PeriodicDownload(
                reactor=self._reactor,
                host=self._adminHostname,
                port=self._adminPort,
                schedule=Schedule(period=SERVICE_POLL_INTERVAL),
                prio=9,
                name='config')
            self._periodicConfigDownloadTree = be(
                (self._configPeriodicDownload,
                    (self._configDownloadProcessor,
                        (self,),
                        (self._serviceLog,),
                    )
                )
            )
        for configObserver in configObservers:
            self.addConfigObserver(configObserver)
        return self._periodicConfigDownloadTree

    def addConfigObserver(self, configObserver):
        self._configDownloadProcessor.addObserver(configObserver)


class DummySelectService(object):
    def updateConfig(self, **kwargs):
        return
        yield