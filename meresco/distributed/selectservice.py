## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from os import makedirs
from os.path import join, isfile, isdir
from random import choice

from seecr.utils import Version

from .service import Service
from socket import socket, error as SocketError, TCP_KEEPIDLE, IPPROTO_TCP, TCP_KEEPINTVL, SOL_SOCKET, SO_KEEPALIVE, TCP_KEEPCNT

class SelectService(object):
    def __init__(self, reactor, currentVersion, statePath=None, services=None, useCache=True):
        self._serviceList = self._ServiceList(reactor)
        self._serviceList.updateConfig(services)
        self._currentVersion = Version.create(currentVersion)
        self._statePath = statePath
        if self._statePath:
            isdir(self._statePath) or makedirs(self._statePath)
        self._chosenService = dict()
        self._cache = dict()
        def setCacheItem(key, value):
            self._cache[key] = value
        self._setCacheItem = setCacheItem if useCache else lambda key, value: None

    def updateConfig(self, **kwargs):
        self._cache.clear()
        yield self._serviceList.updateConfig(**kwargs)

    def selectHostPortForService(self, type, flag, remember=False, endpoint=None, **kwargs):
        return self.selectService(type=type, flag=flag, remember=remember, **kwargs).selectHostAndPort(endpoint)

    def selectService(self, type, flag, remember=False, identifier=None, **kwargs):
        if remember and not identifier:
            identifier = self._getChosenService(type)

        matchingServices = self.findServices(type=type, flag=flag, **kwargs)
        if len(matchingServices) == 0:
            raise ValueError("No '%s' service found" % type)
        if not identifier is None:
            for service in matchingServices:
                if service.identifier == identifier:
                    return service
            raise ValueError("No '%s' service found with identifier '%s'." % (type, identifier))
        service = choice(matchingServices)

        if remember:
            self._setChosenService(type, service.identifier)
        return service

    def hostsAndPortsForService(self, type, flag, endpoint=None, **kwargs):
        for service in self.findServices(type=type, flag=flag, **kwargs):
            yield service.selectHostAndPort(endpoint)

    def findServices(self, type, flag, minVersion=None, untilVersion=None, **ignored):
        key = (type, flag, minVersion, untilVersion)
        matchingServices = self._cache.get(key, [])
        if matchingServices:
            return matchingServices
        minVersion = self._currentVersion.majorVersion() if minVersion is None else Version.create(minVersion)
        untilVersion = minVersion.nextMajorVersion() if untilVersion is None else Version.create(untilVersion)
        for service in self._serviceList.iterServices():
            if service.type == type and flag.isSet(service) and minVersion <= service.getVersion() < untilVersion:
                matchingServices.append(service)
        self._setCacheItem(key, matchingServices)
        return matchingServices

    def _getChosenService(self, type):
        chosenService = self._chosenService.get(type)
        if chosenService is not None:
            return chosenService
        choicefile = join(self._statePath, 'service-%s.choice' % type)
        if isfile(choicefile):
            chosenService = open(choicefile).read().strip()
            self._chosenService[type] = chosenService
            return chosenService

    def setRequestedServiceIdentifier(self, type, identifier):
        self._chosenService[type] = identifier

    def _setChosenService(self, type, identifier):
        chosenService = self._chosenService.get(type)
        if chosenService == identifier:
            return
        with open(join(self._statePath, 'service-%s.choice' % type), 'w') as f:
            f.write(identifier)
        self._chosenService[type] = identifier

    @classmethod
    def forAdmin(cls, serviceRegistry, **kwargs):
        result = cls(reactor=None, useCache=False, **kwargs)
        result._serviceList = serviceRegistry
        result.updateConfig = lambda **kwargs: None
        return result

    class _ServiceList(object):
        def __init__(self, reactor):
            self._reactor = reactor
            self._services = []
            self._soks = []

        def updateConfig(self, services, **kwargs):
            self._services = []
            for sok in self._soks:
                self._reactor.removeReader(sok)
                sok.close()
            self._soks = []
            for serviceDict in services.values():
                service = Service(**serviceDict)
                if service.infoport > 0:
                    self._connect(service)
                self._services.append(service)
            return
            yield

        def iterServices(self):
            return iter([s for s in self._services if not s.get('isDead')])

        def _connect(self, service):
            try:
                sok = self._createSocket(service.selectHostAndPort())
            except SocketError:
                self._markDead(None, service)
            else:
                self._soks.append(sok)
                self._reactor.addReader(sok, lambda: self._markDead(sok, service))

        def _createSocket(self, hostPort):
            sok = socket()
            sok.connect(hostPort)
            sok.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
            sok.setsockopt(IPPROTO_TCP, TCP_KEEPIDLE, 1)
            sok.setsockopt(IPPROTO_TCP, TCP_KEEPINTVL, 1)
            sok.setsockopt(IPPROTO_TCP, TCP_KEEPCNT, 1)
            return sok

        def _markDead(self, sok, service):
            if sok:
                self._reactor.removeReader(sok)
                self._soks.remove(sok)
                sok.close()
            service["isDead"] = True