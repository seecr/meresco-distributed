## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2013, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from urllib.parse import urlencode

from seecr.test import SeecrTestCase, CallTrace

from weightless.core import compose, be

from meresco.core import Observable

from meresco.components.http.utils import CRLF

from meresco.distributed import ConfigHandler

def httpSplit(string):
    return string.split(CRLF*2)

class ConfigHandlerTest(SeecrTestCase):

    def setUp(self):
        SeecrTestCase.setUp(self)

        configHandler = ConfigHandler()
        self.observer = CallTrace(emptyGeneratorMethods=['saveConfig'])

        self.dna = be(
            (Observable(),
                (configHandler,
                    (self.observer,),
                )
            )
        )

    def testShouldHandleUpdatePOST(self):
        session = {}
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/config/update',
            session=session,
            Body=urlencode({"config": '{"aconfig": "avalue"}', "redirectUrl": "/config"}),
            Method='POST')))

        header, body = httpSplit(result)
        self.assertEqual('HTTP/1.0 302 Found\r\nLocation: /config', header)
        self.assertEqual("", body)
        self.assertEqual(['saveConfig'], [m.name for m in self.observer.calledMethods])
        self.assertEqual({'aconfig': 'avalue'}, self.observer.calledMethods[0].kwargs['config'])
        self.assertEqual({'message': {'class': 'success', 'text': 'Configuratie opgeslagen.'}}, session)

    def testShouldHandleSplitUpConfig(self):
        session = {}
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/config/update',
            session=session,
            Body=urlencode({
                "config": '{"aconfig": "avalue"}',
                "config_somename": '{"api.frontend": {"ipAddress": "1.2.3.4"}}',
                "redirectUrl": "/config"
            }),
            Method='POST')))

        header, body = httpSplit(result)
        self.assertEqual('HTTP/1.0 302 Found\r\nLocation: /config', header)
        self.assertEqual("", body)
        self.assertEqual(['saveConfig'], [m.name for m in self.observer.calledMethods])
        self.assertEqual({'aconfig': 'avalue', 'api.frontend':{'ipAddress': '1.2.3.4'}}, self.observer.calledMethods[0].kwargs['config'])
        self.assertEqual({'message': {'class': 'success', 'text': 'Configuratie opgeslagen.'}}, session)

    def testShouldHandleInvalidUpdateAndShowError(self):
        session = {}
        result = ''.join(compose(self.dna.all.handleRequest(
            path='/config/update',
            session=session,
            Body=urlencode({"config": 'NO JSON', "redirectUrl": "/config"}),
            Method='POST')))

        header, body = httpSplit(result)
        self.assertEqual('HTTP/1.0 302 Found\r\nLocation: /config', header)
        self.assertEqual("", body)
        self.assertEqual({'message': {'class': 'error', 'text': 'Ongeldige JSON'}}, session)

    def testShouldDisallowWrongPaths(self):
        result = ''.join(compose(self.dna.all.handleRequest(path='/config/add', arguments={'type': ['srv']}, Method='POST')))

        header, body = httpSplit(result)
        self.assertEqual(header, 'HTTP/1.0 400 Bad Request')
        self.assertEqual(body, '')

    def testShouldOnlyHandlePost(self):
        result = ''.join(compose(self.dna.all.handleRequest(path='/config/update', arguments={}, Method='GET')))
        header, body = httpSplit(result)
        self.assertEqual('HTTP/1.0 405 Method Not Allowed', header)
        self.assertEqual('', body)

        result = ''.join(compose(self.dna.all.handleRequest(path='/config/update', arguments={}, Method='HEAD')))
        header, body = httpSplit(result)
        self.assertEqual('HTTP/1.0 405 Method Not Allowed', header)
        self.assertEqual('', body)

