## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2016, 2018, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
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

from seecr.test import SeecrTestCase, CallTrace

from simplejson import loads, dumps
from urllib.parse import urlencode

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
        self.serviceHandler = ServiceHandler(secret='guessme!', softwareVersion='42')
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
                (self.serviceHandler,
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
        postBody = bytes(urlencode(bodyArgs), encoding='utf-8')
        result = ''.join(compose(self.dna.all.handleRequest(
            path=updatePath,
            Method='POST',
            arguments={},
            Body=postBody,
        )))
        header, body = httpSplit(result)
        self.assertTrue('HTTP/1.0 200', header)

        bodyArgs['hash'] = 'wrong'
        postBody = bytes(urlencode(bodyArgs), encoding='utf-8')
        result = ''.join(compose(self.dna.all.handleRequest(
            path=updatePath,
            Method='POST',
            arguments={},
            Body=postBody,
        )))
        header, body = httpSplit(result)
        self.assertTrue('HTTP/1.0 400', header)
        self.assertEqual('Hash does not match expected hash.', body)

    def testShouldUpdateServicesOnHttpPostRequest(self):
        hash = serviceUpdateHash(secret='guessme!', identifier='cc635329-c089-41a8-91be-2a4554851515', type='srv', ipAddress='127.0.0.1', infoport=1234)
        postBody = bytes(urlencode({
            'identifier': 'cc635329-c089-41a8-91be-2a4554851515',
            'type': 'srv',
            'ipAddress': '127.0.0.1',
            'infoport': '1234',
            'hash': hash,
            'data': dumps({'error': 1, 'VERSION': '2.718281828'}),
        }), encoding='utf-8')
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

        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: application/json; charset=utf-8', header)
        self.assertEqual(
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
    'api_version': 2,
    'software_version': '42',
    'domain': 'seecr.nl'
}, loads(body))

        result = self.serviceRegistry.listServices()
        result['cc635329-c089-41a8-91be-2a4554851515']['lastseen'] = 666.6
        self.assertEqual({
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

        self.assertEqual(['getConfig'], self.configuration.calledMethodNames())
        self.assertEqual(["updateZone"], self.dns.calledMethodNames())
        self.assertEqual([((), {'ipAddress': '127.0.0.1', 'fqdn': 'srv0.seecr.nl'})], [(m.args, m.kwargs) for m in self.dns.calledMethods])

    def testShouldBeAbleToUpdateMultipleServices(self):
        hash = serviceUpdateHash(secret='guessme!', identifier='cc635329-c089-41a8-91be-2a4554851515', type='srv', ipAddress='127.0.0.1', infoport=1234)
        postBody = bytes(urlencode({
            'identifier': 'cc635329-c089-41a8-91be-2a4554851515',
            'type': 'srv',
            'ipAddress': '127.0.0.1',
            'infoport': '1234',
            'hash': hash,
            'data': dumps({'VERSION': '2.718281828'}),
        }), encoding="utf-8")
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/service/v2/update',
            Method='POST',
            arguments={},
            Body=postBody,
        )))

        hash = serviceUpdateHash(secret='guessme!', identifier='11111111-aaaa-3333-eeee-444444444444', type='nice', ipAddress='128.0.0.8', infoport=6666)
        postBody = bytes(urlencode({
            'identifier': '11111111-aaaa-3333-eeee-444444444444',
            'type': 'nice',
            'ipAddress': '128.0.0.8',
            'infoport': '6666',
            'hash': hash,
            'data': dumps({'VERSION': '2.718281828'}),
        }), encoding="utf-8")
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

        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: application/json; charset=utf-8', header)
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
    'api_version': 2,
    'software_version': '42',
    'domain': 'seecr.nl',
}, loads(body))

    def testShouldListMultipleServices(self):
        hash = serviceUpdateHash(secret='guessme!', identifier='cc635329-c089-41a8-91be-2a4554851515', type='srv', ipAddress='127.0.0.1', infoport=1234)
        postBody = bytes(urlencode({
            'identifier': 'cc635329-c089-41a8-91be-2a4554851515',
            'type': 'srv',
            'ipAddress': '127.0.0.1',
            'infoport': '1234',
            'data': dumps({'VERSION': '2.718281828'}),
            'hash': hash,
        }), encoding="utf-8")
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/service/v2/update',
            Method='POST',
            arguments={},
            Body=postBody,
        )))

        hash = serviceUpdateHash(secret='guessme!', identifier='11111111-aaaa-3333-eeee-444444444444', type='nice', ipAddress='128.0.0.8', infoport=6666)
        postBody = bytes(urlencode({
            'identifier': '11111111-aaaa-3333-eeee-444444444444',
            'type': 'nice',
            'ipAddress': '128.0.0.8',
            'infoport': '6666',
            'data': dumps({'VERSION': '2.718281828'}),
            'hash': hash,
        }), encoding="utf-8")
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

        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: application/json; charset=utf-8', header)
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
    'api_version': 2,
    'software_version': '42',
    'domain': 'seecr.nl'
}, loads(body))

    def testShouldHaveGlobalConfigForVersion2(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            arguments={},
            Method='GET',
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEqual(['host', 'port'], sorted(dictBodyV2['config'].keys()))
        self.assertEqual(['api_version', 'config', 'domain', 'services', 'software_version'], sorted(dictBodyV2.keys()))

    def testShouldListOnlyRequestedKeys(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            Method='GET',
            arguments={'keys':['collections']}
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEqual(['api_version', 'collections', 'config', 'domain', 'services', 'software_version'], sorted(dictBodyV2.keys()))

    def testAllKeys(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            Method='GET',
            arguments={'keys':['collections,other']}
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEqual(['api_version', 'collections', 'config', 'domain', 'other', 'services', 'software_version'], sorted(dictBodyV2.keys()))
        self.assertEqual({'collection': {'provenanceSource': 'collection_source', 'enabled': True, 'name': 'collection'}}, dictBodyV2['collections'])
        self.assertEqual(['other'], dictBodyV2['other'])
        self.assertEqual({'host': 'localhost', 'port': 8000}, dictBodyV2['config'])
        self.assertEqual({}, dictBodyV2['services'])

    def testNonexistingKeys(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            Method='GET',
            arguments={'keys':['no']}
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEqual(['api_version', 'config', 'domain', 'errors', 'services', 'software_version'], sorted(dictBodyV2.keys()))
        self.assertEqual(["Key 'no' not found."], dictBodyV2['errors'])

    def testRemovingNotListedKeys(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            Method='GET',
            arguments={'keys':['-no']}
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEqual(['api_version', 'config', 'domain', 'services', 'software_version'], sorted(dictBodyV2.keys()))

    def testAllKeysMultipleArguments(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            Method='GET',
            arguments={'keys':['collections', 'other']}
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEqual(['api_version', 'collections', 'config', 'domain', 'other', 'services', 'software_version'], sorted(dictBodyV2.keys()))

    def testIgnoreDefaultKeys(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            Method='GET',
            arguments={'keys':['collections,-config,-services']}
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEqual(['api_version', 'collections', 'domain', 'software_version'], sorted(dictBodyV2.keys()))

    def testShouldReturnOnlyRequestedKeysWithUpdate(self):
        hash = serviceUpdateHash(secret='guessme!', identifier='cc635329-c089-41a8-91be-2a4554851515', type='srv', ipAddress='127.0.0.1', infoport=1234)
        postBody = bytes(urlencode({
            'identifier': 'cc635329-c089-41a8-91be-2a4554851515',
            'type': 'srv',
            'ipAddress': '127.0.0.1',
            'infoport': '1234',
            'data': dumps({'VERSION': '2.718281828'}),
            'hash': hash,
        }), encoding="utf-8")
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/service/v2/update',
            Method='POST',
            arguments={'keys':['collections']},
            Body=postBody,
        )))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEqual(['api_version', 'collections', 'config', 'domain', 'services', 'software_version', 'this_service'], sorted(dictBodyV2.keys()))

    def testKeysAll(self):
        result = asString(self.dna.all.handleRequest(
            path='/service/v2/list',
            Method='GET',
            arguments={'__all__':['True']}
        ))
        header, body = httpSplit(result)
        dictBodyV2 = JsonDict.loads(body)
        self.assertEqual(['api_version', 'collections', 'config', 'domain', 'other', 'services', 'software_version'], sorted(dictBodyV2.keys()))

    def testShouldNotAllowWrongPath(self):
        result = ''.join(compose(self.dna.all.handleRequest(path='/service/fluffy', arguments={'type': ['srv']}, Method='POST')))

        header, body = httpSplit(result)
        self.assertEqual(header, 'HTTP/1.0 400 Bad Request')
        self.assertEqual(body, '')

    def testShouldAllowPostsOnly(self):
        result = ''.join(compose(self.dna.all.handleRequest(path='/service/v2/update', arguments={}, Method='GET')))
        header, body = httpSplit(result)
        self.assertEqual('HTTP/1.0 405 Method Not Allowed', header)
        self.assertEqual('', body)

        result = ''.join(compose(self.dna.all.handleRequest(path='/service/v2/update', arguments={}, Method='HEAD')))
        header, body = httpSplit(result)
        self.assertEqual('HTTP/1.0 405 Method Not Allowed', header)
        self.assertEqual('', body)

    def testShouldFailOnBadVersion(self):
        result = asString(self.dna.all.handleRequest(path='/service/v42/list', arguments={}, Method='GET'))
        header, body = httpSplit(result)
        self.assertEqual('HTTP/1.0 400 Bad Request', header)
        self.assertEqual('', body)

    def testShouldFailOnMissingParameters(self):
        postBody = bytes(urlencode({
            'identifier': newId(),
        }), encoding="utf-8")
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/service/v2/update',
            Method='POST',
            arguments={},
            Body=postBody,
        )))
        header, body = httpSplit(result)
        self.assertEqual('HTTP/1.0 400 Bad Request', header)
        self.assertEqual("Missing parameter: 'type'", body)

    def testUseVpn(self):
        observer = CallTrace()
        self.dna = be(
            (Observable(),
                (ServiceHandler(secret='guessme!', softwareVersion='42'),
                    (observer,),
                )
            ))

        result = asString(self.dna.all.handleRequest(path='/service/v2/list', arguments={'useVpn': ['True']}, Method='GET'))
        header, body = httpSplit(result)
        self.assertTrue("200 OK" in header, header)
        self.assertEqual({"listServices", "getConfig", 'getDomain'}, set(observer.calledMethodNames()))
        indexListServices = observer.calledMethodNames().index('listServices')
        self.assertEqual({'activeOnly': True, 'convertIpsToVpn': True, 'includeState': False}, observer.calledMethods[indexListServices].kwargs)

newId = lambda: str(uuid4())

def httpSplit(string):
    return string.split(CRLF*2)
