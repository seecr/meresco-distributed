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

from uuid import UUID
from time import time
from copy import deepcopy

from seecr.utils import Version
from meresco.components import parseAbsoluteUrl

from .constants import SERVICE_FLAGS, READABLE, WRITABLE


class Service(dict):
    _REQUIRED_KEYS = set(['identifier', 'type', 'lastseen', 'ipAddress', 'number', 'infoport'])
    _OPTIONAL_KEYS = set(['data', 'longgone']).union(SERVICE_FLAGS)
    _ALL_KEYS = _REQUIRED_KEYS.union(_OPTIONAL_KEYS)

    def __init__(self, domainname=None, timeout=None, ultimateTimeout=None, _time=None, *args, **kwargs):
        super(Service, self).__init__(*args, **kwargs)
        if domainname is not None:
            self._domainname = domainname
        elif 'fqdn' in kwargs:
            self._domainname = kwargs['fqdn'].split('.', 1)[1]
        self._timeout = timeout
        self._ultimateTimeout = ultimateTimeout
        self._privateState = {}
        self._time = _time or time
        for flag in SERVICE_FLAGS.values():
            if flag.name not in self:
                self[flag.name] = flag.default

    def setPrivateFlagValue(self, flag, value):
        self._privateState[flag] = value

    def removePrivateFlag(self, flag):
        del self._privateState[flag]

    def getPrivateState(self):
        state = deepcopy(self._privateState)
        for flag in SERVICE_FLAGS.values():
            if not flag.name in state:
                state[flag.name] = self.get(flag.name, flag.default)
        return state

    def update(self, type, ipAddress, infoport, lastseen, data):
        self['type'] = type
        self['ipAddress'] = ipAddress
        self['infoport'] = infoport
        self['lastseen'] = lastseen
        self['data'] = data

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def disable(self):
        self['longgone'] = True
        self[READABLE.name] = False
        self[WRITABLE.name] = False
        self._privateState = {}

    def enable(self):
        self.pop('longgone', None)

    def isDisabled(self):
        return self.get('longgone', False)

    def isTooLongGone(self):
        return self._ultimateTimeout > 0 and self.lastseen + self._ultimateTimeout < self._now()

    def fqdn(self):
        return "%s%s.%s" % (self.type, self.number, self._domainname)

    def isActive(self, since=None):
        return self.lastseen + self._timeout > (since or self._now())

    def validate(self):
        assert str(UUID(self.identifier)) == self.identifier, "Service identifier must be a uuid"
        missingKeys = self._REQUIRED_KEYS.difference(self.keys())
        assert not missingKeys, "Service %s: %s misses required keys: %s" % (self.identifier, self, missingKeys)
        unknownKeys = set(self.keys()).difference(self._ALL_KEYS)
        assert not unknownKeys, "Service %s: %s contains unrecognized keys: %s" % (self.identifier, self, unknownKeys)

    def enrichAndClone(self, includeState=False):
        copy = Service(
            domainname=self._domainname,
            timeout=self._timeout,
            ultimateTimeout=self._ultimateTimeout,
            _time=self._time,
            **deepcopy(dict(self.items()))
        )
        copy['fqdn'] = self.fqdn()
        copy['active'] = self.isActive()
        copy['lastseen_delta'] = int(self._now() - self.lastseen)
        if includeState:
            copy['state'] = self.getPrivateState()
        return copy

    def getVersion(self):
        return Version(self.data['VERSION'])

    def selectHostAndPort(self, endpoint=None):
        if endpoint is not None:
            try:
                parsedUrl = parseAbsoluteUrl(self.data['endpoints'][endpoint])
                if parsedUrl:
                    return parsedUrl.host, parsedUrl.port
            except KeyError:
                raise ValueError("No endpoint '%s' found for service '%s' with identifier '%s'." % (endpoint, self.type, self.identifier))
        return self.ipAddress, self.infoport

    def _now(self):
        return self._time()
