## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2018, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2021 SURF https://www.surf.nl
# Copyright (C) 2021 Stichting Kennisnet https://www.kennisnet.nl
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

from os.path import join, isfile
from uuid import uuid4

from seecr.test import SeecrTestCase, CallTrace

from weightless.core import be, asString, consume, NoneOfTheObserversRespond, retval
from meresco.core import Observable
from meresco.distributed.constants import WRITABLE, READABLE
from meresco.distributed.utils import usrSharePath
from meresco.distributed.failover import MatchesVersion, Proxy, ServiceConfig
from meresco.distributed.failover._matchesversion import betweenVersionCondition


class MatchesVersionTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.matchesVersion = MatchesVersion(minVersion='1', untilVersion='3')
        self.observer = CallTrace('observer', methods=dict(somemessage=lambda: (x for x in ['result'])), emptyGeneratorMethods=['updateConfig'])
        self.top = be((Observable(),
            (self.matchesVersion,
                (self.observer,)
            )
        ))

    def testDoesNotMatchNoConfig(self):
        self.assertEqual('', asString(self.top.all.somemessage()))
        self.assertEqual([], self.observer.calledMethodNames())

    def testDoesNotMatchNoVersion(self):
        consume(self.matchesVersion.updateConfig(config={'foo': 'bar'}))
        self.assertEqual('', asString(self.top.all.somemessage()))
        self.assertEqual(['updateConfig'], self.observer.calledMethodNames())

    def testDoesNotMatch(self):
        consume(self.matchesVersion.updateConfig(**{'software_version': '0.1', 'config':{'foo': 'bar'}}))
        self.assertEqual('', asString(self.top.all.somemessage()))
        self.assertEqual(['updateConfig'], self.observer.calledMethodNames())

    def testDoesMatch(self):
        consume(self.matchesVersion.updateConfig(software_version='2'))
        self.assertEqual('result', asString(self.top.all.somemessage()))
        self.assertEqual(['updateConfig', 'somemessage'], self.observer.calledMethodNames())

    def testDeterminesConfig(self):
        newId = lambda: str(uuid4())
        services = {
            newId(): {'type': 'service1', 'ipAddress': '10.0.0.2', 'infoport': 1234, 'active': True, 'readable': True, 'writable': True, 'data': {'VERSION': '1.5'}},
            newId(): {'type': 'service2', 'ipAddress': '10.0.0.3', 'infoport': 1235, 'active': True, 'readable': True, 'writable': True, 'data': {'VERSION': '1.8'}},
        }
        config = {
            'service1.frontend': {
                'fqdn': 'service1.front.example.org',
                'ipAddress': '1.2.3.4',
            },
            'service2.frontend': {
                'fqdn': 'service2.front.example.org',
                'ipAddress': '1.2.3.5',
            },
        }
        configFile = join(self.tempdir, 'server.conf')
        top = be(
            (Proxy(nginxConfigFile=configFile),
                (MatchesVersion(
                        minVersion='1.4',
                        untilVersion='2.0'),
                    (ServiceConfig(
                        type='service1',
                        minVersion='1.4',
                        untilVersion='2.0',
                        flag=WRITABLE),
                    ),
                ),
                (MatchesVersion(
                        minVersion='1.4',
                        untilVersion='4.0'),
                    (ServiceConfig(
                        type='service2',
                        minVersion='1.4',
                        untilVersion='2.0',
                        flag=READABLE),
                    )
                )
            )
        )

        mustUpdate, sleeptime = top.update(software_version='3.0', config=config, services=services, verbose=False)
        self.assertTrue(mustUpdate)
        self.assertEqual(30, sleeptime)
        self.assertTrue(isfile(configFile))

        with open(configFile) as fp:
            self.assertEqualText("""## Generated by meresco.distributed.failover.Proxy

upstream __var_3ff29304e7437997bf4171776e1fe282_service2 {
    server 10.0.0.3:1235;
}

server {
    listen 1.2.3.5:80;
    server_name service2.front.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;

    location / {
        proxy_pass http://__var_3ff29304e7437997bf4171776e1fe282_service2;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, fp.read())


    # MatchesVersion is expected to be invoked with 'all', but testing for 'do', 'call' and 'any' invocation just in case

    def testDoesNotMatchDo(self):
        consume(self.matchesVersion.updateConfig(**{'software_version': '0.1'}))
        self.top.do.somemessage()
        self.assertEqual(['updateConfig'], self.observer.calledMethodNames())

    def testDoesMatchDo(self):
        consume(self.matchesVersion.updateConfig(**{'software_version': '2'}))
        self.top.do.anothermessage()
        self.assertEqual(['updateConfig', 'anothermessage'], self.observer.calledMethodNames())

    def testDoesNotMatchCall(self):
        consume(self.matchesVersion.updateConfig(**{'software_version': '0.1'}))
        try:
            _ = self.top.call.somemessage()
            self.fail()
        except NoneOfTheObserversRespond:
            pass
        self.assertEqual(['updateConfig'], self.observer.calledMethodNames())

    def testDoesMatchCall(self):
        consume(self.matchesVersion.updateConfig(**{'software_version': '2'}))
        _ = self.top.call.somemessage()
        self.assertEqual(['updateConfig', 'somemessage'], self.observer.calledMethodNames())

    def testDoesNotMatchAny(self):
        consume(self.matchesVersion.updateConfig(**{'software_version': '0.1'}))
        try:
            _ = retval(self.top.any.somemessage())
            self.fail()
        except NoneOfTheObserversRespond:
            pass
        self.assertEqual(['updateConfig'], self.observer.calledMethodNames())

    def testDoesMatchAny(self):
        consume(self.matchesVersion.updateConfig(**{'software_version': '2'}))
        _ = retval(self.top.any.somemessage())
        self.assertEqual(['updateConfig', 'somemessage'], self.observer.calledMethodNames())

    def testBetweenVersionCondition(self):
        inbetween = betweenVersionCondition('1.3', '8')
        self.assertTrue(inbetween('1.3'))
        self.assertTrue(inbetween('1.3.x'))
        self.assertTrue(inbetween('7.9'))
        self.assertFalse(inbetween('8.0'))
        self.assertFalse(inbetween('8'))
        self.assertFalse(inbetween('77'))
        self.assertFalse(inbetween('1.2.x'))
