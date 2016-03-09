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

from seecr.test import SeecrTestCase, CallTrace
from seecr.test.io import stderr_replaced
from seecr.test.portnumbergenerator import PortNumberGenerator
from seecr.test.mockserver import MockServer

from contextlib import contextmanager
from os import listdir
from os.path import join, isfile, isdir
from socket import timeout
from time import time
from urllib2 import URLError

from weightless.core import compose

from meresco.distributed import ConfigDownloadProcessor

from meresco.components.json import JsonDict
from meresco.distributed.utils import IP_ADDRESS
from meresco.distributed import serviceUpdateHash
from simplejson import loads
from meresco.components.http.utils import CRLF
from urlparse import parse_qs

SHARED_SECRET = 'a very secret secret'
VERSION="41.2"

@contextmanager
def httpResponder(hangupConnectionTimeout=None):
    serverPort = PortNumberGenerator.next()
    ms = MockServer(port=serverPort, hangupConnectionTimeout=hangupConnectionTimeout)
    ms.start()
    try:
        yield ms, serverPort
    finally:
        ms.halt = True


class ConfigDownloadProcessorTest(SeecrTestCase):
    def testShouldCreateStatePathWhenAbsentOnInit(self):
        subpath = join(self.tempdir, 'sub', 'path')
        ConfigDownloadProcessor.forUpdate(identifier='id', type='type', infoport=0, statePath=subpath, sharedSecret=SHARED_SECRET, version=VERSION)
        self.assertTrue(isdir(subpath))

    def testShouldAbortSyncDownloadWhenConnectionFailed(self):
        cdp = ConfigDownloadProcessor.forUpdate(identifier='id', type='type', infoport=0, statePath=self.tempdir, sharedSecret=SHARED_SECRET, version=VERSION)
        cdp.addObserver(CallTrace(returnValues=dict(serviceData={'data': {'error': 0}})))

        with stderr_replaced() as err:
            try:
                t0 = time()
                cdp.download('localhost', 0)
            except URLError, e:
                t1 = time()
                self.assertTrue('Connection refused' in str(e), str(e))
                delta = t1 - t0
                self.assertTrue(0 < delta < 0.1, delta)
            else:
                self.fail('Should not happen.')

            self.assertTrue('URLError (<urlopen error [Errno 111] Connection refused>).\nTried: http://localhost:0/api/service/v2/list?identifier=id&keys=' in err.getvalue(), err.getvalue())
            self.assertTrue('\nConfigDownloadProcessor: configuration cachefile "%s/configuration_cache.json" not found, cannot start!\n' % self.tempdir in err.getvalue(), err.getvalue())

    def testShouldAbortSyncDownloadWhenTimeoutReached(self):
        cdp = ConfigDownloadProcessor.forUpdate(identifier='id', type='type', infoport=12345, statePath=self.tempdir, syncDownloadTimeout=1, sharedSecret=SHARED_SECRET, version=VERSION)
        cdp.addObserver(CallTrace(returnValues=dict(serviceData={'data': {'error': 0}})))
        with stderr_replaced() as err:
            with httpResponder(hangupConnectionTimeout=1.1) as (ms, serverPort):
                try:
                    t0 = time()
                    cdp.download('localhost', serverPort)
                except (URLError, timeout), e:
                    t1 = time()
                    self.assertTrue('timed out' in str(e), str(e))
                    delta = t1 - t0
                    self.assertTrue(0.9 < delta < 1.1, delta)
                else:
                    self.fail('Should not happen.')

            self.assertTrue('timed out' in err.getvalue(), err.getvalue())
            self.assertTrue('Tried: http://localhost:%s/api/service/v2/list?identifier=id&keys=' % serverPort in err.getvalue(), err.getvalue())
            self.assertTrue('\nConfigDownloadProcessor: configuration cachefile "%s/configuration_cache.json" not found, cannot start!\n' % self.tempdir in err.getvalue(), err.getvalue())

    def testShouldAbortSyncDownloadWhenRecievedAWrongHttpResponse(self):
        cdp = ConfigDownloadProcessor.forUpdate(identifier='id', type='type', infoport=0, statePath=self.tempdir, syncDownloadTimeout=1, sharedSecret=SHARED_SECRET, version=VERSION)
        cdp.addObserver(CallTrace(returnValues=dict(serviceData={'data': {'error': 0}})))
        with stderr_replaced() as err:
            with httpResponder() as (ms, serverPort):
                try:
                    ms.response = 'HTTP/1.0 500 Internal Server Stuff\r\n\r\n'
                    t0 = time()
                    cdp.download('localhost', serverPort)
                except URLError, e:
                    t1 = time()
                    self.assertTrue('HTTP Error 500: Internal Server Stuff' in str(e), str(e))
                    delta = t1 - t0
                    self.assertTrue(0.0 < delta < 0.5, delta)
                else:
                    self.fail('Should not happen.')

            self.assertTrue('HTTPError (HTTP Error 500: Internal Server Stuff).\nTried: http://localhost:%s/api/service/v2/list?identifier=id&keys=' % serverPort in err.getvalue(), err.getvalue())
            self.assertTrue('\nConfigDownloadProcessor: configuration cachefile "%s/configuration_cache.json" not found, cannot start!\n' % self.tempdir in err.getvalue(), err.getvalue())

    def testShouldSaveConfigOnSuccesfullDownload(self):
        cdp = ConfigDownloadProcessor.forUpdate(identifier='id', type='type', infoport=0, statePath=self.tempdir, syncDownloadTimeout=1, sharedSecret=SHARED_SECRET, version=VERSION)
        cdp.addObserver(CallTrace(returnValues=dict(serviceData={'data': {'error': 0}})))
        self.assertEquals(0, len(listdir(self.tempdir)))

        mockConfig = {
            "config": {'key': 'value'},
            "services": "stuff",
        }
        with httpResponder() as (ms, serverPort):
            ms.response = 'HTTP/1.0 200 OK.\r\n\r\n%s' % JsonDict(mockConfig).dumps()
            configuration = cdp.download('localhost', serverPort)

        self.assertEquals(mockConfig, configuration)
        cdpConfigFile = join(self.tempdir, 'configuration_cache.json')
        self.assertTrue(isfile(cdpConfigFile))
        self.assertEquals(['configuration_cache.json'], listdir(self.tempdir))
        self.assertEquals(mockConfig, JsonDict().load(open(cdpConfigFile)))

        mockConfig = {
            "config": "Fig",
            "services": "Fuss",
        }
        with httpResponder() as (ms, serverPort):
            ms.response = 'HTTP/1.0 200 OK.\r\n\r\n%s' % JsonDict(mockConfig).dumps()
            configuration = cdp.download('localhost', serverPort)
        self.assertEquals(['configuration_cache.json'], listdir(self.tempdir))
        self.assertEquals(mockConfig, JsonDict().load(open(cdpConfigFile)))

        # Don't overwrite on unparsables
        with httpResponder() as (ms, serverPort):
            ms.response = 'HTTP/1.0 200 OK.\r\n\r\nunparsables'
            try:
                configuration = cdp.download('localhost', serverPort)
            except ValueError, e:

                self.assertTrue(str(e).startswith('No JSON object could be decoded') or str(e).startswith("Expecting value: line 1 column 1 (char 0)"), str(e))
            else:
                self.fail('Should not happen')
        self.assertEquals(mockConfig, JsonDict().load(open(cdpConfigFile)))

    def testShouldSaveConfigOnSuccesfullHandle(self):
        cdp = ConfigDownloadProcessor.forUpdate(identifier='id', type='type', infoport=0, statePath=self.tempdir, sharedSecret=SHARED_SECRET, version=VERSION)

        mockConfig = {
            "config": {'key': 'value'},
            "services": "stuff",
        }
        observer = CallTrace('Observer', emptyGeneratorMethods=['updateConfig'])
        cdp.addObserver(observer)
        self.assertEquals([], listdir(self.tempdir))

        list(compose(cdp.handle(data=JsonDict(mockConfig).dumps())))

        self.assertEquals(['configuration_cache.json'], listdir(self.tempdir))
        cdpConfigFile = join(self.tempdir, 'configuration_cache.json')
        self.assertEquals(mockConfig, JsonDict().load(open(cdpConfigFile)))
        self.assertEquals(['updateConfig'], observer.calledMethodNames())

        # Don't overwrite on unparsables
        try:
            list(compose(cdp.handle(data='unparsables')))
        except ValueError, e:
            self.assertTrue(str(e).startswith('No JSON object could be decoded') or str(e).startswith("Expecting value: line 1 column 1 (char 0)"), str(e))
        else:
            self.fail('Should not happen')
        self.assertEquals(mockConfig, JsonDict().load(open(cdpConfigFile)))

    def testShouldReUseSavedConfigOnFailedDownload(self):
        cdpConfigFile = join(self.tempdir, 'configuration_cache.json')
        mockConfig = {'config': 'con', 'services': 'ser'}
        with open(cdpConfigFile, 'w') as f:
            JsonDict(mockConfig).dump(f)

        with stderr_replaced() as err:
            with httpResponder(hangupConnectionTimeout=1.2) as (ms, serverPort):
                cdp = ConfigDownloadProcessor.forUpdate(identifier='id', type='type', infoport=serverPort, statePath=self.tempdir, syncDownloadTimeout=1, sharedSecret=SHARED_SECRET, version=VERSION)
                cdp.addObserver(CallTrace(returnValues=dict(serviceData={'data': {'error': 0}})))
                configuration = cdp.download('localhost', serverPort)

            self.assertTrue('timed out' in err.getvalue(), err.getvalue())
            self.assertTrue('Tried: http://localhost:%s/api/service/v2/list?identifier=id&keys=' % serverPort in err.getvalue(), err.getvalue())

            self.assertTrue('\nConfigDownloadProcessor: configuration cachefile "%s/configuration_cache.json" found, starting.\n' % self.tempdir in err.getvalue(), err.getvalue())

        self.assertEquals(mockConfig, configuration)

    def testUpdateConfig(self):
        cdp = ConfigDownloadProcessor.forUpdate(identifier='id', type='type', infoport=0, statePath=self.tempdir, sharedSecret=SHARED_SECRET, version=VERSION)
        observer = CallTrace('observer', emptyGeneratorMethods=['updateConfig'])
        cdp.addObserver(observer)
        list(compose(cdp.updateConfig(config={'some': 'stuff'}, services={'xyz': {'abc': 'def'}})))
        self.assertEquals(['updateConfig'], observer.calledMethodNames())
        self.assertEquals({'config': {'some': 'stuff'}, 'services': {'xyz': {'abc': 'def'}}}, observer.calledMethods[0].kwargs)

    def testBuildRequest(self):
        # Used by PeriodicDownload
        parameters = dict(identifier='id1', type='api', ipAddress='127.0.0.1', infoport=12345)
        downloadProcessor = ConfigDownloadProcessor.forUpdate(statePath=self.tempdir, keys=['collections', 'apiKeys'], sharedSecret=SHARED_SECRET, version=VERSION, **parameters)
        def serviceData(dataDict):
            dataDict['error'] = 0
        downloadProcessor.addObserver(CallTrace(methods={'serviceData': serviceData}))
        header, request = downloadProcessor.buildRequest().split(CRLF*2)
        self.assertEquals('POST /api/service/v2/update?keys=apiKeys%%2Ccollections HTTP/1.0\r\nContent-Length: %s\r\nUser-Agent: api id1 v%s' % (len(request), VERSION), header)
        arguments = parse_qs(request)
        self.assertEquals([serviceUpdateHash(secret=SHARED_SECRET, **parameters)], arguments.pop('hash'))
        data = loads(arguments.pop('data')[0])
        self.assertEquals(dict((k,[str(v)]) for k,v in parameters.items()), arguments)
        self.assertEquals(VERSION, data['VERSION'])
        self.assertEquals(0, data['error'])
        self.assertTrue(data['uptime'] >= 0)

    def testBuildRequestForDownload(self):
        # Used by PeriodicDownload
        downloadProcessor = ConfigDownloadProcessor.forDownload(statePath=self.tempdir, keys=['collections', 'apiKeys'], type="Loadbalancer", identifier='1234-1234', sharedSecret=SHARED_SECRET, version=VERSION)
        header, request = downloadProcessor.buildRequest().split(CRLF*2)
        self.assertEquals('GET /api/service/v2/list?identifier=1234-1234&keys=apiKeys%%2Ccollections HTTP/1.0\r\nUser-Agent: Loadbalancer 1234-1234 v%s' % VERSION, header)

    def testBuildRequestForDownloadWithIdentifier(self):
        # Used by PeriodicDownload
        downloadProcessor = ConfigDownloadProcessor.forDownload(statePath=self.tempdir, keys=['collections', 'apiKeys'], identifier='12345678-1234-1234-1234-1234567890ab', type='api', sharedSecret=SHARED_SECRET, version=VERSION)
        header, request = downloadProcessor.buildRequest().split(CRLF*2)
        self.assertEquals('GET /api/service/v2/list?identifier=12345678-1234-1234-1234-1234567890ab&keys=apiKeys%%2Ccollections HTTP/1.0\r\nUser-Agent: api 12345678-1234-1234-1234-1234567890ab v%s' % VERSION, header)

    def testBuildRequestWithIpAddressDefault(self):
        parameters = dict(identifier='id1', type='api', infoport=12345)
        downloadProcessor = ConfigDownloadProcessor.forUpdate(statePath=self.tempdir, sharedSecret=SHARED_SECRET, version=VERSION, **parameters)

        header, request = downloadProcessor.buildRequest().split(CRLF*2)
        arguments = parse_qs(request)
        self.assertEquals(IP_ADDRESS, arguments['ipAddress'][0])

    def testHandle(self):
        observer = CallTrace(emptyGeneratorMethods=['updateConfig'])
        downloadProcessor = ConfigDownloadProcessor.forUpdate(identifier='id1', type='api', ipAddress='127.0.0.1', infoport='12345', statePath=self.tempdir, sharedSecret=SHARED_SECRET, version=VERSION)
        downloadProcessor.addObserver(observer)

        list(compose(downloadProcessor.handle(data='{"config": {"key1": "value1", "key2": "value2"}, "services": {"xyz": "abc"}}')))
        self.assertEquals(['updateConfig'], observer.calledMethodNames())
        self.assertEquals({"key1": "value1", "key2": "value2"}, observer.calledMethods[0].kwargs['config'])
        self.assertEquals({"xyz": "abc"}, observer.calledMethods[0].kwargs['services'])

    def testAdditionalData(self):
        parameters = dict(identifier='id1', type='api', ipAddress='127.0.0.1', infoport=12345)
        downloadProcessor = ConfigDownloadProcessor.forUpdate(statePath=self.tempdir, endpoints={'triplestore': 'http://example.org:876/sparql'}, keys=['collections', 'apiKeys'], sharedSecret=SHARED_SECRET, version=VERSION, **parameters)
        def serviceData(dataDict):
            dataDict['error'] = 0
        downloadProcessor.addObserver(CallTrace(methods={'serviceData': serviceData}))
        header, request = downloadProcessor.buildRequest().split(CRLF*2)
        self.assertEquals('POST /api/service/v2/update?keys=apiKeys%%2Ccollections HTTP/1.0\r\nContent-Length: %s\r\nUser-Agent: api id1 v%s' % (len(request), VERSION), header)
        arguments = parse_qs(request)
        data = loads(arguments.pop('data')[0])
        self.assertEquals(dict(triplestore='http://example.org:876/sparql'), data['endpoints'])

    def testDownloadWithoutStatepath(self):
        cdp = ConfigDownloadProcessor.forDownload(statePath=None, version=VERSION)
        mockConfig = {
            "config": {'key': 'value'},
            "services": "stuff",
        }
        with httpResponder() as (ms, serverPort):
            ms.response = 'HTTP/1.0 200 OK.\r\n\r\n%s' % JsonDict(mockConfig).dumps()
            configuration = cdp.download('localhost', serverPort)

        self.assertEquals(mockConfig, configuration)

    def testDownloadFailsIfNoHttpResponse(self):
        cdp = ConfigDownloadProcessor.forDownload(statePath=None, version=VERSION)
        with stderr_replaced():
            with httpResponder(hangupConnectionTimeout=1.2) as (ms, serverPort):
                self.assertRaises(Exception, lambda: cdp.download('localhost', serverPort))

    def testUseVpn(self):
        parameters = dict(identifier='id1', type='api', ipAddress='127.0.0.1', infoport=12345)
        downloadProcessor = ConfigDownloadProcessor.forUpdate(statePath=self.tempdir, useVpn=True, sharedSecret=SHARED_SECRET, version=VERSION, **parameters)
        header, request = downloadProcessor.buildRequest().split(CRLF*2)
        self.assertEquals('POST /api/service/v2/update?keys=&useVpn=True HTTP/1.0\r\nContent-Length: %s\r\nUser-Agent: api id1 v%s' % (len(request), VERSION), header)
