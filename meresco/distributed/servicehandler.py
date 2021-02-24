## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2018, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015, 2018, 2021 Stichting Kennisnet https://www.kennisnet.nl
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

from urllib.parse import parse_qs
from simplejson import loads

from weightless.core import NoneOfTheObserversRespond
from meresco.core import Observable
from meresco.components.http.utils import CRLF, Ok
from meresco.components.json import JsonDict

from meresco.distributed import serviceUpdateHash


class ServiceHandler(Observable):
    versions = {'v2': 2}
    default_version = 2

    def __init__(self, secret, softwareVersion=None, name=None):
        Observable.__init__(self, name=name)
        self._secret = secret
        self._softwareVersion = softwareVersion
        self._prefix = '/service/'
        self._actions = {
            'update': (self.handleUpdate, 'POST'),
            'list': (self.handleList, 'GET'),
        }

    def handleRequest(self, **kwargs):
        Method = kwargs.get('Method')
        path = kwargs.get('path')
        try:
            _, prefix, tail = path.partition(self._prefix)
            if prefix != self._prefix:
                raise Exception('Expected ' + self._prefix)
            if '/' not in tail:
                raise Exception('Expected something like /api/service/v2/list')
            version, action = tail.split('/')
            version = self.versions[version]
            handleFunction, methodForAction = self._actions[action]
            if Method != methodForAction:
                raise Exception('METHOD_NOT_ALLOWED')
        except Exception as e:
            if str(e) == 'METHOD_NOT_ALLOWED':
                yield 'HTTP/1.0 405 Method Not Allowed' + CRLF*2
            else:
                yield badRequest
            return
        yield handleFunction(apiVersion=version, **kwargs)

    def handleUpdate(self, Body, **kwargs):
        bodyArgs = parse_qs(str(Body, encoding='utf-8'))
        try:
            identifier = bodyArgs['identifier'][0]
            type = bodyArgs['type'][0]
            ipAddress = bodyArgs['ipAddress'][0]
            infoport = int(bodyArgs['infoport'][0])
            hash = bodyArgs['hash'][0]
            data = loads(bodyArgs.get('data', ["{}"])[0])
            self._verifyHash(hash=hash, identifier=identifier, type=type, ipAddress=ipAddress, infoport=infoport)
            self.call.updateService(identifier=identifier, type=type, ipAddress=ipAddress, infoport=infoport, data=data)
        except KeyError as e:
            yield badRequest
            yield "Missing parameter: %s" % str(e)
            return
        except ValueError as e:
            yield badRequest
            yield str(e)
            return
        yield self._httpConfigAndServices(serviceIdentifier=identifier, **kwargs)

    def handleList(self, **kwargs):
        serviceIdentifier = kwargs['arguments'].get('identifier', [None])[0]
        yield self._httpConfigAndServices(serviceIdentifier=serviceIdentifier, **kwargs)

    def _verifyHash(self, hash, **kwargs):
        expectedHash = serviceUpdateHash(self._secret, **kwargs)
        if hash != expectedHash:
            raise ValueError('Hash does not match expected hash.')

    def _httpConfigAndServices(self, apiVersion, arguments, serviceIdentifier=None, prettyPrint=False, **ignored):
        result = {}
        additionalConfigDict = result
        fullServiceInfo = arguments.get('allServiceInfo', ['False'])[0] == 'True'
        useVpn = arguments.get('useVpn', ['False'])[0] == 'True'
        retrieveAll = arguments.get('__all__', ['False'])[0] == 'True'
        keys = self._allKeys() if retrieveAll else self._keysFromArgs(arguments)
        for key in _requestedKeys(keys):
            try:
                if key == 'services':
                    additionalConfigDict[key] = self.call.listServices(activeOnly=not fullServiceInfo, includeState=fullServiceInfo, convertIpsToVpn=useVpn)
                elif key == 'config':
                    additionalConfigDict[key] = self.call.getConfig()
                else:
                    additionalConfigDict[key] = self.call[key].getConfiguration(allConfiguration=retrieveAll)
            except NoneOfTheObserversRespond:
                result.setdefault('errors', []).append("Key '%s' not found." % key)
        if serviceIdentifier:
            this_service = self.call.getService(identifier=serviceIdentifier)
            if this_service is not None:
                result['this_service'] = this_service
                result['this_service']['state'] = self.call.getPrivateStateFor(identifier=serviceIdentifier)
        result = JsonDict(api_version=apiVersion, domain=self.call.getDomain(), **result)
        if self._softwareVersion is not None:
            result['software_version'] = self._softwareVersion
        yield okJson
        yield result.pretty_print() if prettyPrint else str(result)

    def _keysFromArgs(self, arguments):
        return (k for c in arguments.get('keys', []) for k in c.split(',') if k)

    def _allKeys(self):
        return (name for name in (o.observable_name() for o in self.observers()) if name)


def _requestedKeys(keys):
    requested = set(['config', 'services'])
    for key in keys:
        if not key:
            continue
        if key.startswith('-'):
            requested.discard(key[1:])
        else:
            requested.add(key)
    return requested


badRequest = 'HTTP/1.0 400 Bad Request' + CRLF*2
okJson = Ok + \
         "Content-Type: application/json; charset=utf-8" + CRLF*2
