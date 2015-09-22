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

from seecr.test import SeecrTestCase, CallTrace

from simplejson import loads, dumps
from urllib import urlencode

from weightless.core import compose, be, asString

from meresco.core import Observable
from meresco.distributed import serviceUpdateHash

from meresco.components.http.utils import CRLF

from meresco.components.json import JsonDict
from meresco.distributed import ServiceHandler, ServiceRegistry

from uuid import uuid4


class ServiceHandlerTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        serviceHandler = ServiceHandler(secret='guessme!')
        self.serviceRegistry = ServiceRegistry(stateDir=self.tempdir, domainname='seecr.nl', reactor=CallTrace())
        self.config = {"host": "localhost", "port": 8000}
        self.configuration = CallTrace('configuration', methods={'getConfig': lambda: JsonDict(self.config)}, ignoredAttributes=['getConfiguration', 'updateZone', 'deleteFromZone', 'call_unknown'])
        self.dns = CallTrace("dns")
        self.collections = CallTrace("provenanceWhitelist", returnValues={'getConfiguration': {
            'collection': {'name': 'collection', 'provenanceSource': 'collection_source', 'enabled': True}}, 'observable_name': 'collections'},
            ignoredAttributes=['call_unknown'])
        self.other = CallTrace("other", returnValues={'getConfiguration': ['other'], 'observable_name': 'other'}, ignoredAttributes=['call_unknown'])

        self.dna = be(
            (Observable(),
                (serviceHandler,
                    (self.serviceRegistry,
                        (self.dns,),
                    ),
                    (self.configuration,),
                    (self.collections,),
                    (self.other,),
                )
            )
        )

    def testShouldValidateHashOnUpdate(self):
        updatePath = '/service/v2/update'
        hash = serviceUpdateHash(secret='guessme!', identifier='cc635329-c089-41a8-91be-2a4554851515', type='srv', ipAddress='127.0.0.1', infoport=1234)
        bodyArgs = {
            'identifier': 'cc635329-c089-41a8-91be-2a4554851515',
            'type': 'srv',
            'ipAddress': '127.0.0.1',
            'infoport': '1234',
            'hash': hash,
            'data': dumps({'VERSION': '2.718281828'}),
        }
        postBody = urlencode(bodyArgs)
        result = ''.join(compose(self.dna.all.handleRequest(
            path=updatePath,
            Method='POST',
            arguments={},
            Body=postBody,
        )))
        header, body = httpSplit(result)
        self.assertTrue('HTTP/1.0 200', header)

        bodyArgs['hash'] = 'wrong'
        postBody = urlencode(bodyArgs)
        result = ''.join(compose(self.dna.all.handleRequest(
            path=updatePath,
            Method='POST',
            arguments={},
            Body=postBody,
        )))
        header, body = httpSplit(result)
        self.assertTrue('HTTP/1.0 400', header)
        self.assertEquals('Hash does not match expected hash.', body)

    def testShouldUpdateServicesOnHttpPostRequest(self):
        hash = serviceUpdateHash(secret='guessme!', identifier='cc635329-c089-41a8-91be-2a4554851515', type='srv', ipAddress='127.0.0.1', infoport=1234)
        postBody = urlencode({
            'identifier': 'cc635329-c089-41a8-91be-2a4554851515',
            'type': 'srv',
            'ipAddress': '127.0.0.1',
            'infoport': '1234',
            'hash': hash,
            'data': dumps({'error': 1, 'VERSION': '2.718281828'}),
        })
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/service/v2/update',
            Method='POST',
            arguments={},
            Body=postBody,
        )))

        header, body = httpSplit(result)
        dictBody = JsonDict.loads(body)
        lastseen = dictBody['services']['cc635329-c089-41a8-91be-2a4554851515']['lastseen']
        body = dictBody.pretty_print()

        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: application/json; charset=utf-8', header)
        self.assertEquals(
{
    "services": {
        "cc635329-c089-41a8-91be-2a4554851515": {
            "type": "srv",
            "fqdn": "srv0.seecr.nl",
            "identifier": "cc635329-c089-41a8-91be-2a4554851515",
            "number": 0,
            "lastseen": lastseen,
            "lastseen_delta": 0,
            "active": True,
            "ipAddress": "127.0.0.1",
            "infoport": 1234,
            'readable': False,
            'writable': False,
            'data': {'error': 1, 'VERSION': '2.718281828'}
        }
    },
    "this_service": {
        "type": "srv",
        "fqdn": "srv0.seecr.nl",
        "identifier": "cc635329-c089-41a8-91be-2a4554851515",
        "number": 0,
        "lastseen": lastseen,
        "lastseen_delta": 0,
        "active": True,
        "ipAddress": "127.0.0.1",
        "infoport": 1234,
        'readable': False,
        'writable': False,
        "state": {
            'readable': False,
            'writable': False,
        },
        'data': {'error': 1, 'VERSION': '2.718281828'}
    },
    "config": {
        "host": "localhost",
        "port": 8000
    },
    'api_version':2
}, loads(body))

        result = self.serviceRegistry.listServices()
        result['cc635329-c089-41a8-91be-2a4554851515']['lastseen'] = 666.6
        self.assertEquals({
            'cc635329-c089-41a8-91be-2a4554851515': {
                'type': 'srv',
                'fqdn': 'srv0.seecr.nl',
                "identifier": "cc635329-c089-41a8-91be-2a4554851515",
                'number': 0,
                'lastseen': 666.6,
                "lastseen_delta": 0,
                'active': True,
                'ipAddress': '127.0.0.1',
                'infoport': 1234,
                'readable': False,
                'writable': False,
                'data': {'error': 1, 'VERSION': '2.718281828'}}
            }, result)

        self.assertEquals(['getConfig'], self.configuration.calledMethodNames())
        self.assertEquals(["updateZone"], self.dns.calledMethodNames())
        self.assertEquals([((), {'ipAddress': '127.0.0.1', 'fqdn': 'srv0.seecr.nl'})], [(m.args, m.kwargs) for m in self.dns.calledMethods])

    def testShouldBeAbleToUpdateMultipleServices(self):
        hash = serviceUpdateHash(secret='guessme!', identifier='cc635329-c089-41a8-91be-2a4554851515', type='srv', ipAddress='127.0.0.1', infoport=1234)
        postBody = urlencode({
            'identifier': 'cc635329-c089-41a8-91be-2a4554851515',
            'type': 'srv',
            'ipAddress': '127.0.0.1',
            'infoport': '1234',
            'hash': hash,
            'data': dumps({'VERSION': '2.718281828'}),
        })
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/service/v2/update',
            Method='POST',
            arguments={},
            Body=postBody,
        )))

        hash = serviceUpdateHash(secret='guessme!', identifier='11111111-aaaa-3333-eeee-444444444444', type='nice', ipAddress='128.0.0.8', infoport=6666)
        postBody = urlencode({
            'identifier': '11111111-aaaa-3333-eeee-444444444444',
            'type': 'nice',
            'ipAddress': '128.0.0.8',
            'infoport': '6666',
            'hash': hash,
            'data': dumps({'VERSION': '2.718281828'}),
        })
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/service/v2/update',
            Method='POST',
            arguments={},
            Body=postBody,
        )))

        header, body = httpSplit(result)
        dictBody = JsonDict.loads(body)
        lastseenCC = dictBody['services']['cc635329-c089-41a8-91be-2a4554851515']['lastseen']
        lastseen11 = dictBody['services']['11111111-aaaa-3333-eeee-444444444444']['lastseen']
        body = dictBody.pretty_print()

        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: application/json; charset=utf-8', header)
        self.assertDictEquals(
{
    "services": {
        "11111111-aaaa-3333-eeee-444444444444": {
            "type": "nice",
            "fqdn": "nice0.seecr.nl",
            'identifier': '11111111-aaaa-3333-eeee-444444444444',
            "number": 0,
            "lastseen": lastseen11,
            "lastseen_delta": 0,
            "active": True,
            "ipAddress": "128.0.0.8",
            "infoport": 6666,
            'readable': False,
            'writable': False,
            'data': {'VERSION': '2.718281828'}
        },
        "cc635329-c089-41a8-91be-2a4554851515": {
            "type": "srv",
            "fqdn": "srv0.seecr.nl",
            'identifier': 'cc635329-c089-41a8-91be-2a4554851515',
            "number": 0,
            "lastseen": lastseenCC,
            "lastseen_delta": 0,
            "active": True,
            "ipAddress": "127.0.0.1",
            "infoport": 1234,
            'readable': False,
            'writable': False,
            'data': {'VERSION': '2.718281828'}
        }
    },
    "config": {
        "host": "localhost",
        "port": 8000,
    },
    "this_service": {
        "type": "nice",
        "fqdn": "nice0.seecr.nl",
        "identifier": "11111111-aaaa-3333-eeee-444444444444",
        "number": 0,
        "lastseen": lastseen11,
            "lastseen_delta": 0,
        "active": True,
        "ipAddress": "128.0.0.8",
        "infoport": 6666,
        'readable': False,
        'writable': False,
        "state":{
            'readable': False,
            'writable': False,
        },
        'data': {'VERSION': '2.718281828'}
    },
    'api_version':2,
}, loads(body))

    def testShouldListMultipleServices(self):
        hash = serviceUpdateHash(secret='guessme!', identifier='cc635329-c089-41a8-91be-2a4554851515', type='srv', ipAddress='127.0.0.1', infoport=1234)
        postBody = urlencode({
            'identifier': 'cc635329-c089-41a8-91be-2a4554851515',
            'type': 'srv',
            'ipAddress': '127.0.0.1',
            'infoport': '1234',
            'data': dumps({'VERSION': '2.718281828'}),
            'hash': hash,
        })
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/service/v2/update',
            Method='POST',
            arguments={},
            Body=postBody,
        )))

        hash = serviceUpdateHash(secret='guessme!', identifier='11111111-aaaa-3333-eeee-444444444444', type='nice', ipAddress='128.0.0.8', infoport=6666)
        postBody = urlencode({
            'identifier': '11111111-aaaa-3333-eeee-444444444444',
            'type': 'nice',
            'ipAddress': '128.0.0.8',
            'infoport': '6666',
            'data': dumps({'VERSION': '2.718281828'}),
            'hash': hash,
        })
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/service/v2/update',
            Method='POST',
            arguments={},
            Body=postBody,
        )))
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/service/v2/list',
            arguments={'identifier': ['11111111-aaaa-3333-eeee-444444444444'], 'allServiceInfo': ['True']},
            Method='GET',
        )))

        header, body = httpSplit(result)
        dictBody = JsonDict.loads(body)
        lastseenCC = dictBody['services']['cc635329-c089-41a8-91be-2a4554851515']['lastseen']
        lastseen11 = dictBody['services']['11111111-aaaa-3333-eeee-444444444444']['lastseen']
        body = dictBody.pretty_print()

        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: application/json; charset=utf-8', header)
        self.assertDictEquals(
{
    "services": {
        "11111111-aaaa-3333-eeee-444444444444": {
            "type": "nice",
            "fqdn": "nice0.seecr.nl",
            "identifier": "11111111-aaaa-3333-eeee-444444444444",
            "number": 0,
            "lastseen": lastseen11,
            "lastseen_delta": 0,
            "active": True,
            "ipAddress": "128.0.0.8",
            "infoport": 6666,
            'readable': False,
            'writable': False,
            "state":{
                'readable': False,
                'writable': False,
            },
            'data': {'VERSION': '2.718281828'}
        },
        "cc635329-c089-41a8-91be-2a4554851515": {
            "type": "srv",
            "fqdn": "srv0.seecr.nl",
            "identifier": "cc635329-c089-41a8-91be-2a4554851515",
            "number": 0,
            "lastseen": lastseenCC,
            "lastseen_delta": 0,
            "active": True,
            "ipAddress": "127.0.0.1",
            "infoport": 1234,
            'readable': False,
            'writable': False,
            "state":{
                'readable': False,
                'writable': False,
            },
            'data': {'VERSION': '2.718281828'}
        }
    },
    "config": {
        "host": "localhost",
        "port": 8000,
    },
    "this_service": {
        "type": "nice",
        "fqdn": "nice0.seecr.nl",
        "identifier": "11111111-aaaa-3333-eeee-444444444444",
        "number": 0,
        "lastseen": lastseen11,
        "lastseen_delta": 0,
        "active": True,
        "ipAddress": "128.0.0.8",
        "infoport": 6666,
        'readable': False,
        'writable': False,
        "state":{
            'readable': False,
            'writable': False,
        },
        'data': {'VERSION': '2.718281828'}
    },
    'api_version':2,
}, loads(body))

    def testShouldHaveGlobalConfigForVersion2(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            arguments={},
            Method='GET',
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEquals(['host', 'port'], sorted(dictBodyV2['config'].keys()))
        self.assertEquals(['api_version', 'config', 'services',], sorted(dictBodyV2.keys()))

    def testShouldListOnlyRequestedKeys(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            Method='GET',
            arguments={'keys':['collections']}
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEquals(['api_version', 'collections', 'config', 'services',], sorted(dictBodyV2.keys()))

    def testAllKeys(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            Method='GET',
            arguments={'keys':['collections,other']}
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEquals(['api_version', 'collections', 'config', 'other', 'services'], sorted(dictBodyV2.keys()))
        self.assertEquals({'collection': {'provenanceSource': 'collection_source', 'enabled': True, 'name': 'collection'}}, dictBodyV2['collections'])
        self.assertEquals(['other'], dictBodyV2['other'])
        self.assertEquals({'host': 'localhost', 'port': 8000}, dictBodyV2['config'])
        self.assertEquals({}, dictBodyV2['services'])

    def testNonexistingKeys(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            Method='GET',
            arguments={'keys':['no']}
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEquals(['api_version', 'config', 'errors', 'services'], sorted(dictBodyV2.keys()))
        self.assertEquals(["Key 'no' not found."], dictBodyV2['errors'])

    def testRemovingNotListedKeys(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            Method='GET',
            arguments={'keys':['-no']}
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEquals(['api_version', 'config', 'services'], sorted(dictBodyV2.keys()))

    def testAllKeysMultipleArguments(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            Method='GET',
            arguments={'keys':['collections', 'other']}
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEquals(['api_version', 'collections', 'config', 'other', 'services'], sorted(dictBodyV2.keys()))

    def testIgnoreDefaultKeys(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            Method='GET',
            arguments={'keys':['collections,-config,-services']}
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEquals(['api_version', 'collections'], sorted(dictBodyV2.keys()))

    def testShouldReturnOnlyRequestedKeysWithUpdate(self):
        hash = serviceUpdateHash(secret='guessme!', identifier='cc635329-c089-41a8-91be-2a4554851515', type='srv', ipAddress='127.0.0.1', infoport=1234)
        postBody = urlencode({
            'identifier': 'cc635329-c089-41a8-91be-2a4554851515',
            'type': 'srv',
            'ipAddress': '127.0.0.1',
            'infoport': '1234',
            'data': dumps({'VERSION': '2.718281828'}),
            'hash': hash,
        })
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/service/v2/update',
            Method='POST',
            arguments={'keys':['collections']},
            Body=postBody,
        )))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEquals(['api_version', 'collections', 'config', 'services', 'this_service'], sorted(dictBodyV2.keys()))

    def testShouldNotAllowWrongPath(self):
        result = ''.join(compose(self.dna.all.handleRequest(path='/service/fluffy', arguments={'type': ['srv']}, Method='POST')))

        header, body = httpSplit(result)
        self.assertEquals(header, 'HTTP/1.0 400 Bad Request')
        self.assertEquals(body, '')

    def testShouldAllowPostsOnly(self):
        result = ''.join(compose(self.dna.all.handleRequest(path='/service/v2/update', arguments={}, Method='GET')))
        header, body = httpSplit(result)
        self.assertEquals('HTTP/1.0 405 Method Not Allowed', header)
        self.assertEquals('', body)

        result = ''.join(compose(self.dna.all.handleRequest(path='/service/v2/update', arguments={}, Method='HEAD')))
        header, body = httpSplit(result)
        self.assertEquals('HTTP/1.0 405 Method Not Allowed', header)
        self.assertEquals('', body)

    def testShouldFailOnBadVersion(self):
        result = asString(self.dna.all.handleRequest(path='/service/v42/list', arguments={}, Method='GET'))
        header, body = httpSplit(result)
        self.assertEquals('HTTP/1.0 400 Bad Request', header)
        self.assertEquals('', body)

    def testShouldFailOnMissingParameters(self):
        postBody = urlencode({
            'identifier': newId(),
        })
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/service/v2/update',
            Method='POST',
            arguments={},
            Body=postBody,
        )))
        header, body = httpSplit(result)
        self.assertEquals('HTTP/1.0 400 Bad Request', header)
        self.assertEquals("Missing parameter: 'type'", body)


newId = lambda: str(uuid4())

def httpSplit(string):
    return string.split(CRLF*2)
