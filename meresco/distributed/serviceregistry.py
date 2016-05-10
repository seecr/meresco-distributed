## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2016 Seecr (Seek You Too B.V.) http://seecr.nl
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

from os import rename, stat
from os.path import join, isfile

import re

from time import time

from uuid import UUID

from meresco.core import Observable
from meresco.components.json import JsonDict, JsonList
from meresco.distributed.constants import ADMIN_DOWNLOAD_PERIOD_CONFIG_KEY, SERVICE_POLL_INTERVAL
from .constants import SERVICE_TIMEOUT, ULTIMATE_TIMEOUT, SERVICE_FLAGS, RETAIN_AFTER_STARTUP_TIMEOUT
from .service import Service


class ServiceRegistry(Observable):
    def __init__(self, reactor, stateDir, domainname, serviceTimeout=None, ultimateTimeout=None, retainAfterStartupTimeout=None, name=None):
        Observable.__init__(self, name=name)
        self._reactor = reactor
        self._jsonFilepath = join(stateDir, SERVICEREGISTRY_FILE)
        self._domainname = domainname
        self._timeout = firstNotNone(serviceTimeout, SERVICE_TIMEOUT)
        self._ultimateTimeout = firstNotNone(ultimateTimeout, ULTIMATE_TIMEOUT)
        self._retainAfterStartupTimeout = firstNotNone(retainAfterStartupTimeout, RETAIN_AFTER_STARTUP_TIMEOUT)
        self._startUpTime = self._now()
        self._shutdownTime = modifiedTime(self._jsonFilepath)
        self._services = self._load()
        self._servicePollInterval = SERVICE_POLL_INTERVAL
        self._timers = {}

    def updateConfig(self, config):
        self._servicePollInterval = config.get(ADMIN_DOWNLOAD_PERIOD_CONFIG_KEY, SERVICE_POLL_INTERVAL)
        return
        yield

    def updateService(self, identifier, type, ipAddress, infoport, data):
        self._disableLongGoneService()
        identifier = str(UUID(identifier))
        if not TYPE_RE.match(type):
            raise ValueError('Service type "%s" must not end with a number.' % type)
        service = self._services.get(identifier)
        if service is None:
            timeout=self._timeout if 'updateInterval' not in data else 2 * data['updateInterval']
            service = Service(
                    identifier=identifier,
                    number=self._newNumber(type),
                    domainname=self._domainname,
                    timeout=timeout,
                    ultimateTimeout=self._ultimateTimeout,
                    _time=self._now,
                )
            self._services[service.identifier] = service
        service.update(type=type, ipAddress=ipAddress, infoport=infoport, lastseen=self._now(), data=data)
        self._applyWaitingFlagSet(service)
        self._save()
        self.do.updateZone(fqdn=service.fqdn(), ipAddress=ipAddress)

    def deleteService(self, identifier):
        self.do.deleteFromZone(fqdn=self._services[identifier].fqdn())
        del self._services[identifier]
        self._save()

    def getDomain(self):
        return self._domainname

    def listServices(self, activeOnly=True, includeState=False, **kwargs):
        self._disableLongGoneService()
        servicesDict = {}
        for identifier, service in self._services.items():
            isActive = service.isActive() or self._isActiveJustAfterStartup(service)
            if activeOnly and (not isActive or service.isDisabled()):
                continue
            servicesDict[identifier] = service.enrichAndClone(includeState=includeState)
        return servicesDict

    def iterServices(self):
        return self.listServices().values()

    def getService(self, identifier):
        self._disableLongGoneService()
        if identifier not in self._services:
            return None
        return self._services[identifier].enrichAndClone()

    def setFlag(self, identifier, flag, value, immediate=False):
        if not flag in SERVICE_FLAGS.values():
            raise ValueError("flag '%s' not known." % flag)
        service = self._services.get(identifier)
        if service is None:
            raise ValueError("service '%s' unknown.")
        if service.isDisabled():
            raise ValueError("service '%s' is too long gone. Reanable it first.")

        if value:
            service.setPrivateFlagValue(flag.name, True)
            service.setPrivateFlagValue(flag.name + GOINGUP_POSTFIX, True)
            if immediate:
                self._reallySetFlag(service, flag)
            return

        service[flag.name] = False
        self._save()
        service.setPrivateFlagValue(flag.name, True)
        service.setPrivateFlagValue(flag.name + GOINGUP_POSTFIX, False)
        def flagChangeProcessed():
            self._flagChangeProcessed(service, flag.name)
        if immediate:
            flagChangeProcessed()
        else:
            self._timers[identifier + "_" + flag.name] = self._reactor.addTimer(self._servicePollInterval, flagChangeProcessed)

    def _applyWaitingFlagSet(self, service):
        privateState = service.getPrivateState()
        for flag in SERVICE_FLAGS.values():
            if privateState.get(flag.name + GOINGUP_POSTFIX):
                self._reallySetFlag(service, flag)

    def _reallySetFlag(self, service, flag):
        service[flag.name] = True
        self._save()
        self._flagChangeProcessed(service, flag.name)

    def _flagChangeProcessed(self, service, flagName):
        self._removeTimer(service.identifier + '_' + flagName)
        service.removePrivateFlag(flagName)
        service.removePrivateFlag(flagName + GOINGUP_POSTFIX)

    def _removeTimer(self, timerId):
        token = self._timers.pop(timerId, None)
        if token:
            try:
                self._reactor.removeTimer(token)
            except ValueError:
                pass

    def reEnableService(self, identifier):
        self._services[identifier].enable()
        self._save()

    def getPrivateStateFor(self, identifier):
        service = self._services.get(identifier)
        if service is None:
            return
        return service.getPrivateState()

    def _isActiveJustAfterStartup(self, service):
        since = self._shutdownTime
        if self._startUpTime + self._retainAfterStartupTimeout < self._now():
            since = None
        isActive = service.isActive(since=since)
        return isActive

    def _newNumber(self, type):
        usedNumbers = [service.number for service in self._services.values() if service.type == type]
        newNumber = 0
        while newNumber in usedNumbers:
            newNumber += 1
        return newNumber

    def _disableLongGoneService(self):
        for service in self._services.values():
            if service.isTooLongGone():
                service.disable()
        self._save()

    def _load(self):
        if not isfile(self._jsonFilepath):
            return {}
        data = open(self._jsonFilepath).read().strip()
        result = {}
        if '[' != data[0]:
            for identifier, serviceDict in JsonDict.loads(data).items():
                service = Service(domainname=self._domainname, timeout=self._timeout, identifier=identifier, ultimateTimeout=self._ultimateTimeout, **serviceDict)
                service.validate()
                result[service.identifier] = service
            return result
        for service in (Service(domainname=self._domainname, timeout=self._timeout, ultimateTimeout=self._ultimateTimeout, **item) for item in JsonList.loads(data)):
            service.validate()
            result[service.identifier] = service
        return result

    def _save(self):
        tmpFile = self._jsonFilepath + '.tmp'
        with open(tmpFile, 'w') as f:
            JsonList([service for service in self._services.values()]).dump(f)
        rename(tmpFile, self._jsonFilepath)

    def _now(self):
        return time()

def firstNotNone(*args):
    for a in args:
        if a is not None:
            return a

def modifiedTime(filepath):
    if not isfile(filepath):
        return None
    return stat(filepath).st_mtime


SERVICEREGISTRY_FILE = 'serviceregistry.json'
TYPE_RE = re.compile(r'^.*[^0-9]$')
GOINGUP_POSTFIX = "_goingup"
