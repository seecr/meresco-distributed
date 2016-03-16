## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.components import PeriodicDownload
from meresco.core import Observable
from meresco.distributed import CompositeState
from meresco.oai import OaiDownloadProcessor
from meresco.distributed.constants import READABLE
from os.path import join

class UpdateMultiplePeriodicDownload(Observable):

    def __init__(self, reactor, serviceManagement, createDownloadObserver, downloadPath, metadataPrefix, statePath, serviceType, set=None, userAgentAddition=None, **kwargs):
        Observable.__init__(self, **kwargs)
        self._reactor = reactor
        self._serviceManagement = serviceManagement
        self._createDownloadObserver = createDownloadObserver
        self._serviceType = serviceType
        self._downloadPath = downloadPath
        self._metadataPrefix = metadataPrefix
        self._set = set
        self._statePath = statePath
        self._userAgentAddition = userAgentAddition
        self._states = {}
        self._oaiDownloads = []

    def updateConfig(self, **kwargs):
        serviceSelector = self._serviceManagement.getServiceSelector()
        for service in serviceSelector.findServices(type=self._serviceType, flag=READABLE):
            if service.identifier not in self._states:
                self._createDownloader(service.identifier)
        return
        yield

    def _createDownloader(self, serviceIdentifier):
        periodicDownload = PeriodicDownload(self._reactor, autoStart=False)
        oaiDownload = OaiDownloadProcessor(
                path=self._downloadPath,
                metadataPrefix=self._metadataPrefix,
                set=self._set,
                workingDirectory=join(self._statePath, serviceIdentifier, self.observable_name()),
                xWait=True,
                name='{}-{}-{}-{}'.format(self._serviceType, serviceIdentifier, self.observable_name(), self._metadataPrefix),
                autoCommit=False,
                userAgentAddition=self._userAgentAddition,
            )

        updatePeriodicDownload = self._serviceManagement.makeUpdatePeriodicDownload(
                sourceServiceIdentifier=serviceIdentifier,
                sourceServiceType=self._serviceType,
                periodicDownload=periodicDownload,
            )
        self._serviceManagement.addConfigObserver(updatePeriodicDownload)
        self._createDownloadObserver(identifier=serviceIdentifier, name=self.observable_name(), periodicDownload=periodicDownload, oaiDownload=oaiDownload)
        self._states[serviceIdentifier] = CompositeState(periodicDownload.getState(), oaiDownload.getState())
        self._oaiDownloads.append(oaiDownload)

    def commit(self):
        for oaiDownloads in self._oaiDownloads:
            oaiDownloads.commit()

    def getState(self):
        return self._states.values()
