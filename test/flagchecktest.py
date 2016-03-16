## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2014-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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
from weightless.core import be, asString, consume
from meresco.core import Observable
from meresco.distributed.constants import READABLE
from meresco.distributed.flagcheck import FlagCheck


class FlagCheckTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.flagCheck = FlagCheck(serviceIdentifier='identifier', flag=READABLE)
        def handleRequest(**kwargs):
            yield 'HTTP/1.0 200 Ok\r\nContent-Type: plain/text\r\n\r\nRESULT'
        self.observer = CallTrace(emptyGeneratorMethods=['someMessage'], methods={'handleRequest':handleRequest})
        self.server = be((Observable(),
            (self.flagCheck,
                (self.observer,),
            )
        ))

    def testAllowedWhenFlagSet(self):
        consume(self.flagCheck.updateConfig(this_service={'readable': False, 'state':{'readable': True}}))
        consume(self.server.all.someMessage(ignored='ignored'))
        self.assertEquals(['someMessage'], self.observer.calledMethodNames())

    def testNotAllowedServiceDoesntExists(self):
        consume(self.flagCheck.updateConfig(this_service=None))
        try:
            consume(self.server.all.someMessage(ignored='ignored'))
            self.fail()
        except EnvironmentError, e:
            self.assertEquals("'someMessage' is not allowed at the moment (readable=False).", str(e))

    def testNotAllowedWhenFlagByDefault(self):
        try:
            consume(self.server.all.someMessage(ignored='ignored'))
            self.fail()
        except EnvironmentError, e:
            self.assertEquals("'someMessage' is not allowed at the moment (readable=False).", str(e))

    def testHandleRequestNotAllowed(self):
        consume(self.flagCheck.updateConfig(this_service={'readable':True, 'state':{'readable':False}}))
        result = asString(self.server.all.handleRequest(ignored='ignored', arguments={}, Headers={}))
        self.assertEquals('HTTP/1.0 503 Service Temporarily Unavailable\r\n\r\n', result)

    def testHandleRequestDisableFlagWithDebugOption(self):
        consume(self.flagCheck.updateConfig(this_service={'readable': True, 'state':{'readable':False}}))
        header, body = asString(self.server.all.handleRequest(ignored='ignored', arguments=dict(debug=['True']), Headers={}, Client=('host', 1234))).split('\r\n\r\n')
        self.assertEquals('RESULT', body)
        self.assertEquals(['handleRequest'], self.observer.calledMethodNames())
        self.assertFalse('debug' in self.observer.calledMethods[0].kwargs['arguments'])

    def testDebugFlagIsRememberedWithCookie(self):
        consume(self.flagCheck.updateConfig(this_service={'readable': True, 'state':{'readable':False}}))
        header, body = asString(self.server.all.handleRequest(ignored='ignored', arguments=dict(debug=['True']), Headers={}, Client=('host', 1234))).split('\r\n\r\n')
        self.assertEquals('RESULT', body)
        headers = parseHeaders(header)
        self.assertTrue('Set-Cookie' in headers,headers)
        self.assertTrue('Expires=' in headers['Set-Cookie'])
        header, body = asString(self.server.all.handleRequest(ignored='ignored', arguments={}, Headers={'Cookie': ';'.join([headers['Set-Cookie'], 'other=cookie'])}, Client=('host', 1234))).split('\r\n\r\n')
        self.assertEquals('RESULT', body)
        self.assertEquals(['handleRequest', 'handleRequest'], self.observer.calledMethodNames())

def parseHeaders(header):
    return dict([i.strip() for i in line.split(':', 1)] for line in header.split('\r\n') if ':' in line)