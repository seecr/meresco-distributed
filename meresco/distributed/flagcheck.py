## begin license ##
#
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  a project of the Koninklijke Bibliotheek
#  and provides a search service for all public
#  libraries in the Netherlands.
#
# Copyright (C) 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
#
# This file is part of "NBC+ (Zoekplatform BNL)"
#
# "NBC+ (Zoekplatform BNL)" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "NBC+ (Zoekplatform BNL)" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "NBC+ (Zoekplatform BNL)"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from time import time
from string import ascii_letters, digits
from hashlib import sha1
from random import choice

from seecr.zulutime import ZuluTime

from weightless.core import compose
from meresco.core import Observable
from meresco.components.http.utils import insertHeader
from meresco.components import TimedDictionary


class FlagCheck(Observable):
    def __init__(self, serviceIdentifier, flag, name=None):
        Observable.__init__(self, name=name)
        self._serviceIdentifier = serviceIdentifier
        self._flag = flag
        self._flagSet = flag.default
        self._seed = randomWord(20)
        self._cookiekey = 'flagcheck%s=' % randomWord(10)
        self._debugTimeout = 60
        self._debugIds = TimedDictionary(self._debugTimeout)

    def updateConfig(self, this_service=None, **kwargs):
        state = {} if this_service is None else this_service.get('state', {})
        self._flagSet = self._flag.isSet(state)
        return
        yield

    def handleRequest(self, arguments, Headers, **kwargs):
        debugId = self._getDebugId(Headers)
        debug = arguments.pop('debug', [None])[0] is not None or debugId
        if not debug:
            try:
                self._check(message='handleRequest')
                yield self.all.handleRequest(arguments=arguments, Headers=Headers, **kwargs)
            except EnvironmentError:
                yield 'HTTP/1.0 503 Service Temporarily Unavailable\r\n\r\n'
        else:
            debugId = self._registerDebugId(debugId=debugId, **kwargs)
            yield insertHeader(
                    compose(self.all.handleRequest(arguments=arguments, Headers=Headers, **kwargs)),
                    extraHeader='Set-Cookie: '+'; '.join([
                            self._cookiekey+debugId,
                            'Expires={0}'.format(self._zulutime().add(seconds=2*self._debugTimeout).rfc1123()),
                        ])
                )

    def _zulutime(self):
        return ZuluTime()

    def _getDebugId(self, Headers):
        debugIds = [cookie.split(self._cookiekey)[-1].strip() for cookie in Headers.get('Cookie','').split(';') if cookie.strip().startswith(self._cookiekey)]
        if len(debugIds) == 1:
            return self._debugIds.get(debugIds[0])
        return None

    def _registerDebugId(self, debugId, Client, **ignored):
        if debugId is None:
            clientaddress, ignoredPort = Client
            debugId = sha1(('%s%s%s%s' % (time(), randomWord(10), clientaddress, self._seed)).encode()).hexdigest()
            self._debugIds[debugId] = debugId
        else:
            self._debugIds.touch(debugId)
        return debugId

    def all_unknown(self, message, **kwargs):
        self._check(message=message)
        yield self.all.unknown(message, **kwargs)

    def _check(self, message):
        if not self._flagSet:
            raise EnvironmentError("'%s' is not allowed at the moment (%s=False)." % (message, self._flag))


def randomWord(length):
    return ''.join(choice(ascii_letters+digits) for i in range(length))
