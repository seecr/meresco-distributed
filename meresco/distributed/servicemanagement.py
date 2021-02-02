## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015-2018, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2015, 2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2017 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2021 SURF https://www.surf.nl
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

import re

from simplejson import loads

from seecr.zulutime import ZuluTime

from seecr.weblib import seecrWebLibPath

from weightless.core import be
from weightless.http import httpget
from meresco.core import Transparent
from meresco.components import Schedule, PeriodicDownload
from meresco.components import Bucket
from meresco.components.http import PathFilter, PathRename, StringServer, FileServer, StaticFiles
from meresco.components.http.utils import ContentTypePlainText
from meresco.components.json import JsonDict
from meresco.html import DynamicHtml
from meresco.oaicommon import stamp2zulutime, ResumptionToken

from meresco.distributed.utils import ipsAndRanges, dynamicPath, staticPath
from meresco.distributed.flagcheck import FlagCheck
from ._serviceflags import WRITABLE, READABLE
from .selectservice import SelectService
from .servicelog import ServiceLog
from .constants import SERVICE_POLL_INTERVAL, ADMIN_DOWNLOAD_PERIOD_CONFIG_KEY
from .updateperiodicdownload import UpdatePeriodicDownload
from .updateips import UpdateIps


class ServiceManagement(object):
    def __init__(self, reactor, admin, configDownloadProcessor, identifier, serviceType, statePath, version=None, documentationPath=None, enableSelectService=True, name=None):
        self._reactor = reactor
        self._adminHostname, self._adminPort = admin
        self._name = name
        self._versionPrefix = '' if not self._name else ('%s-' % self._name)
        self.identifier = identifier
        self._serviceType = serviceType
        self._version = version
        self._selectService = SelectService(statePath=statePath, currentVersion=self._version) if enableSelectService else DummySelectService()
        self._latestConfiguration = JsonDict({})
        self._configDownloadProcessor = configDownloadProcessor
        self._documentationPath = documentationPath
        self._serviceLog = ServiceLog(identifier=identifier)
        self.ipsAndRanges = ipsAndRanges
        self._this_service = Bucket()
        self.allAdditionalGlobals={
            'VERSION': self._version,
            'SERVICE_TYPE': self._serviceType,
            'processingStates': [],
            'ResumptionToken': ResumptionToken,
            'stamp2zulutime': stamp2zulutime,
            'ValueError': ValueError,
            'getattr': getattr,
            'hasattr': hasattr,
            'JsonDict': JsonDict,
            'httpget': httpget,
            'loads': loads,
            'identifier': self.identifier,
            'ZuluTime': ZuluTime,
            're': re,
            'datastreamStates': [],
            'this_service': self.this_service,
        }
        self.commonDynamicPaths = [dynamicPath]
        self.commonStaticPaths = [staticPath, seecrWebLibPath]
        self.createConfigUpdateTree()

    def updateConfig(self, config, **kwargs):
        yield self._selectService.updateConfig(config=config, **kwargs)
        self._configPeriodicDownload.setSchedule(
            Schedule(period=float(config.get(ADMIN_DOWNLOAD_PERIOD_CONFIG_KEY, SERVICE_POLL_INTERVAL)))
        )
        self._this_service = Bucket(**kwargs.get('this_service', {}))
        self._latestConfiguration = JsonDict(config=config, **kwargs)
        return

    def getServiceSelector(self):
        return self._selectService

    @property
    def serviceIdentifier(self):
        return "%s-%s" % (self._serviceType, self.identifier)

    def createConfigUpdateTree(self, configObservers=None):
        configObservers = configObservers or []
        if not getattr(self, '_configPeriodicDownload', None):
            self._configPeriodicDownload = be(
                (PeriodicDownload(
                        reactor=self._reactor,
                        host=self._adminHostname,
                        port=self._adminPort,
                        schedule=Schedule(period=SERVICE_POLL_INTERVAL),
                        prio=9,
                        name='config'),
                    (self._configDownloadProcessor,
                        (self,),
                    )
                )
            )
        for configObserver in configObservers:
            self.addConfigObserver(configObserver)
        return self._configPeriodicDownload

    def addConfigObserver(self, configObserver):
        self._configDownloadProcessor.addObserver(configObserver)

    def makeUpdatePeriodicDownload(self, sourceServiceType, periodicDownload, pollIntervalConfigSelector=None, **kwargs):
        return be(
            (UpdatePeriodicDownload(
                    serviceIdentifier=self.identifier,
                    periodicDownloadName=periodicDownload.observable_name(),
                    pollIntervalConfigSelector=pollIntervalConfigSelector,
                    sourceServiceType=sourceServiceType,
                    **kwargs
                ),
                (self.getServiceSelector(),),
                (periodicDownload,),
            )
        )

    def makeUpdateIps(self, configSelector, component, staticIpAddresses=None):
        return be(
            (UpdateIps(configSelector=configSelector, staticIpAddresses=staticIpAddresses, ipsAndRanges=self.ipsAndRanges),
                (component,)
            )
        )

    def writableCheck(self):
        return self._flagCheck(flag=WRITABLE)

    def readableCheck(self):
        return self._flagCheck(flag=READABLE)

    def createInfoHelix(self, dynamicPath, additionalGlobals=None, observers=None):
        dynamicPaths = dynamicPath if isinstance(dynamicPath, list) else [dynamicPath]
        _observers = Transparent()
        allAdditionalGlobals = dict(self.allAdditionalGlobals)
        if additionalGlobals:
            allAdditionalGlobals.update(additionalGlobals)
        if observers:
            for observer in observers:
                _observers.addObserver(observer)
        staticElement, staticElementPaths = self.createNewStyleStaticElement()
        return \
            (PathFilter('/info'),
                (PathRename(lambda path: path[len('/info'):] or '/'),
                    (PathFilter('/version'),
                        (StringServer("%s%s (%s)" % (self._versionPrefix, self._serviceType, self._version), ContentTypePlainText),)
                    ),
                    (PathFilter('/identifier'),
                        (StringServer(self.identifier, ContentTypePlainText),)
                    ),
                    self.createStaticHelix(),
                    (staticElement,),
                    (PathFilter('/', excluding=[
                            '/version',
                            '/identifier',
                            '/static',
                        ] + staticElementPaths),
                        (DynamicHtml(
                                dynamicPaths + self.commonDynamicPaths,
                                reactor=self._reactor,
                                indexPage='/info/index',
                                additionalGlobals=allAdditionalGlobals,
                            ),
                            (self.configReadObject(),),
                            (self._serviceLog,),
                            (_observers,),
                        )
                    ),
                ),
            )

    @staticmethod
    def createInfoRedirectHelix(excluding=None):
        excluding = [] if excluding is None else excluding
        excluding.extend(['/info', '/static'])
        return  \
            (PathFilter('/', excluding=excluding),
                (SimpleServer("HTTP/1.0 302 Found\r\nLocation: /info\r\n\r\n"), )
            )

    def createStaticHelix(self, staticPath=None):
        paths = [] if staticPath is None else [staticPath]
        paths.extend(self.commonStaticPaths)
        return \
            (PathFilter('/static'),
                (PathRename(lambda path: path[len('/static'):]),
                    (FileServer(paths),)
                )
            )

    def createNewStyleStaticElement(self):
        staticElementPaths = []
        staticElement = Transparent()
        js = lambda p: '/usr/share/javascript/' + p
        for elem in [
                    StaticFiles(libdir=js('jquery'), path='/jquery'),
                    StaticFiles(libdir=js('autosize'), path='/autosize'),
                ]:
            staticElementPaths.append(elem.path)
            staticElement.addObserver(elem)
        return staticElement, staticElementPaths

    def configReadObject(self):
        class ConfigReadObject(object):
            def getConfiguration(inner, **kwargs):
                return self._latestConfiguration
        return ConfigReadObject()

    def _flagCheck(self, flag):
        check = FlagCheck(serviceIdentifier=self.identifier, flag=flag)
        self.addConfigObserver(check)
        return check

    def this_service(self):
        return self._this_service


class SimpleServer(object):
    def __init__(self, completeHttpResponse):
        self._response = completeHttpResponse

    def handleRequest(self, *args, **kwargs):
        yield self._response


class DummySelectService(object):
    def updateConfig(self, **kwargs):
        return
        yield
