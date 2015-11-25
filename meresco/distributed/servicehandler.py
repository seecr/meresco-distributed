## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
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

from meresco.components.http.utils import CRLF, Ok

from meresco.components.json import JsonDict
from meresco.distributed import serviceUpdateHash
from simplejson import loads
from urlparse import parse_qs
from weightless.core import NoneOfTheObserversRespond


class ServiceHandler(Observable):
    versions = {'v2': 2}
    default_version = 2

    def __init__(self, secret, name=None):
        Observable.__init__(self, name=name)
        self._secret = secret
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
        except Exception, e:
            if str(e) == 'METHOD_NOT_ALLOWED':
                yield 'HTTP/1.0 405 Method Not Allowed' + CRLF*2
            else:
                yield badRequest
            return
        yield handleFunction(apiVersion=version, requestedKeys=requestedKeys(kwargs['arguments']), **kwargs)

    def handleUpdate(self, Body, **kwargs):
        bodyArgs = parse_qs(Body)
        try:
            identifier = bodyArgs['identifier'][0]
            type = bodyArgs['type'][0]
            ipAddress = bodyArgs['ipAddress'][0]
            infoport = int(bodyArgs['infoport'][0])
            hash = bodyArgs['hash'][0]
            data = loads(bodyArgs.get('data', ["{}"])[0])
            self._verifyHash(hash=hash, identifier=identifier, type=type, ipAddress=ipAddress, infoport=infoport)
            self.call.updateService(identifier=identifier, type=type, ipAddress=ipAddress, infoport=infoport, data=data)
        except KeyError, e:
            yield badRequest
            yield "Missing parameter: %s" % str(e)
            return
        except ValueError, e:
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

    def _httpConfigAndServices(self, apiVersion, requestedKeys, arguments, serviceIdentifier=None, prettyPrint=False, **ignored):
        result = {}
        additionalConfigDict = result
        fullServiceInfo = arguments.get('allServiceInfo', ['False'])[0] == 'True'
        useVpn = arguments.get('useVpn', ['False'])[0] == 'True'
        for key in requestedKeys:
            try:
                if key == 'services':
                    additionalConfigDict[key] = self.call.listServices(activeOnly=not fullServiceInfo, includeState=fullServiceInfo, convertIpsToVpn=useVpn)
                elif key == 'config':
                    additionalConfigDict[key] = self.call.getConfig()
                else:
                    additionalConfigDict[key] = self.call[key].getConfiguration()
            except NoneOfTheObserversRespond:
                result.setdefault('errors', []).append("Key '%s' not found." % key)
        if serviceIdentifier:
            this_service = self.call.getService(identifier=serviceIdentifier)
            if this_service is not None:
                result['this_service'] = this_service
                result['this_service']['state'] = self.call.getStateFor(identifier=serviceIdentifier)
        result = JsonDict(api_version=apiVersion, **result)
        yield okJson
        yield result.pretty_print() if prettyPrint else str(result)


def requestedKeys(arguments):
    requested = set(['config', 'services'])
    for key in (k for c in arguments.get('keys', []) for k in c.split(',') if k):
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
