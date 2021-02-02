## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015-2018, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2015, 2021 Stichting Kennisnet https://www.kennisnet.nl
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

from os import makedirs
from os.path import join, isfile, isdir
from random import choice

from meresco.components.version import Version
from seecr.utils import atomic_write, readFromFile

from .service import Service


class SelectService(object):
    def __init__(self, currentVersion, statePath=None, services=None, useCache=True, untilVersion=None):
        self._serviceList = self._ServiceList(services)
        self._currentVersion = Version.create(currentVersion)
        self._untilVersion = self._currentVersion.nextMajorVersion() if untilVersion is None else Version.create(untilVersion)
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

        matchingServices = self.findServices(type=type, flag=flag, identifier=identifier, **kwargs)
        if len(matchingServices) == 0:
            if identifier is not None:
                raise ValueError("No '%s' service found with identifier '%s'." % (type, identifier))
            raise ValueError("No '%s' service found" % type)
        service = choice(matchingServices)

        if remember:
            self._setChosenService(type, service.identifier)
        return service

    def hostsAndPortsForService(self, type, flag, endpoint=None, **kwargs):
        for service in self.findServices(type=type, flag=flag, **kwargs):
            yield service.selectHostAndPort(endpoint)

    def findServices(self, type, flag, minVersion=None, untilVersion=None, identifier=None, **ignored):
        key = (type, flag, minVersion, untilVersion, identifier)
        matchingServices = self._cache.get(key, [])
        if matchingServices:
            return matchingServices
        minVersion = self._currentVersion.majorVersion() if minVersion is None else Version.create(minVersion)
        untilVersion = self._untilVersion.majorVersion() if untilVersion is None else Version.create(untilVersion)
        for service in self._serviceList.iterServices():
            if service.type == type and flag.isSet(service) and minVersion <= service.getVersion() < untilVersion:
                if identifier is not None and service.identifier != identifier:
                    continue
                matchingServices.append(service)
        self._setCacheItem(key, matchingServices)
        return matchingServices

    def _getChosenService(self, type):
        chosenService = self._chosenService.get(type)
        if chosenService is not None:
            return chosenService
        choicefile = join(self._statePath, 'service-%s.choice' % type)
        if isfile(choicefile):
            chosenService = readFromFile(choicefile).strip()
            self._chosenService[type] = chosenService
            return chosenService

    def setRequestedServiceIdentifier(self, type, identifier):
        self._chosenService[type] = identifier

    def _setChosenService(self, type, identifier):
        chosenService = self._chosenService.get(type)
        if chosenService == identifier:
            return
        with atomic_write(join(self._statePath, 'service-%s.choice' % type)) as f:
            f.write(identifier)
        self._chosenService[type] = identifier

    @classmethod
    def forAdmin(cls, serviceRegistry, **kwargs):
        result = cls(useCache=False, **kwargs)
        result._serviceList = serviceRegistry
        result.updateConfig = lambda **kwargs: None
        return result


    class _ServiceList(object):
        def __init__(self, services):
            self._services = [] if services is None else services

        def updateConfig(self, services, **kwargs):
            self._services = [Service(**serviceDict) for serviceDict in services.values()]
            return
            yield

        def iterServices(self):
            return iter(self._services)
