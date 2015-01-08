## begin license ##
#
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  a project of the Koninklijke Bibliotheek
#  and provides a search service for all public
#  libraries in the Netherlands.
# This package provides loadbalancer scripts
#
# Copyright (C) 2012-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
#
# This file is part of "NBC+ (Zoekplatform BNL) Loadbalancer"
#
# "NBC+ (Zoekplatform BNL) Loadbalancer" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "NBC+ (Zoekplatform BNL) Loadbalancer" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "NBC+ (Zoekplatform BNL) Loadbalancer"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from seecr.test import SeecrTestCase

from zploadbalancer.failover import NginxConfig
from zploadbalancer.failover.utils import usrSharePath
from os import stat
from os.path import isfile, join
from uuid import uuid4

newId = lambda: str(uuid4())

class NginxConfigTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)

    def testShouldNotWriteNginxConfigFileIfNothingChanged(self):
        services={
            newId(): {'type':'api', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'data':{'VERSION': VERSION}},
        }
        config={
            'api.frontend': {
                'ipAddress': '10.2.3.4',
                'fqdn': 'api.front.example.org',
                'reconfiguration.interval': 20,
            }
        }

        n1 = NginxConfig(type='api', nginxConfigDir=self.tempdir, minVersion=VERSION, untilVersion=VERSION_PLUS_ONE)
        mustUpdate, sleeptime = n1.updateConfig(services=services, config=config)
        self.assertTrue(mustUpdate)
        self.assertEquals(20, sleeptime)
        self.assertTrue(isfile(join(self.tempdir, 'api.frontend.conf')))
        stats = stat(join(self.tempdir, 'api.frontend.conf'))

        n2 = NginxConfig(type='api', nginxConfigDir=self.tempdir, minVersion=VERSION, untilVersion=VERSION_PLUS_ONE)
        mustUpdate, sleeptime = n2.updateConfig(config=config, services=services)
        self.assertFalse(mustUpdate)
        self.assertEquals(stats, stat(join(self.tempdir, 'api.frontend.conf')))

    def testShouldUseNameIfGiven(self):
        services={
            newId(): {'type':'api', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'data':{'VERSION': VERSION}},
        }
        config={
            'api.frontend': {
                'ipAddress': '10.2.3.4',
                'fqdn': 'api.front.example.org',
                'reconfiguration.interval': 20,
            }
        }

        n1 = NginxConfig(type='api', name='api_14', nginxConfigDir=self.tempdir, minVersion=VERSION, untilVersion=VERSION_PLUS_ONE)
        mustUpdate, sleeptime = n1.updateConfig(config=config, services=services)
        self.assertTrue(mustUpdate)
        self.assertEquals(20, sleeptime)
        self.assertTrue(isfile(join(self.tempdir, 'api_14.frontend.conf')))

    def testNameCheck(self):
        def name(name):
            return NginxConfig(type='api', name=name, nginxConfigDir=self.tempdir, minVersion=VERSION, untilVersion=VERSION_PLUS_ONE)
        self.assertRaises(ValueError, name, 'api.1.4')
        self.assertRaises(ValueError, name, 'api.1$%_4')

        self.assertTrue(name('api_14'))


    def testShouldConfigureApiServers(self):
        n = NginxConfig(type='api', name='name', nginxConfigDir=self.tempdir, minVersion=VERSION, untilVersion=VERSION_PLUS_ONE)
        mustUpdate, sleeptime = n.updateConfig(
            services={
                newId(): {'type':'api', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'api', 'ipAddress':'10.0.0.3', 'infoport':2345, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'plein', 'ipAddress':'10.0.0.4', 'infoport':2346, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
            },
            config={
                'api.frontend': {
                    'ipAddress': '10.2.3.4',
                    'fqdn': 'api.front.example.org',
                }
            }
        )
        self.assertEquals(True, mustUpdate)
        self.assertTrue(isfile(join(self.tempdir, 'name.frontend.conf')))
        self.assertEquals("""## Generated by zploadbalancer.failover.NginxConfig
upstream __var_name {
    server 10.0.0.2:1234;
    server 10.0.0.3:2345;
}

server {
    listen 10.2.3.4:80;
    server_name api.front.example.org;
    location / {
        proxy_pass http://__var_name;
        proxy_set_header    Host $host;
        proxy_set_header    X-Real-IP $remote_addr;
        proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(join(self.tempdir, 'name.frontend.conf')).read())

    def testShouldConfigureAnyGivenTypeOfServiceWithPort(self):
        n = NginxConfig(type='other', nginxConfigDir=self.tempdir, minVersion=VERSION, untilVersion=VERSION_PLUS_ONE)
        mustUpdate, sleeptime = n.updateConfig(
            services={
                newId(): {'type':'other', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'other', 'ipAddress':'10.0.0.4', 'infoport':1235, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'other', 'ipAddress':'10.0.0.5', 'infoport':1236, 'active':True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'api', 'ipAddress':'10.0.0.3', 'infoport':2345, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
            },
            config={
                'other.frontend': {
                    'ipAddress': '10.3.4.5',
                    'port': 8080,
                    'fqdn': 'other.front.example.org',
                }
            }
        )
        self.assertEquals(True, mustUpdate)
        self.assertTrue(isfile(join(self.tempdir, 'other.frontend.conf')))
        self.assertEquals("""## Generated by zploadbalancer.failover.NginxConfig
upstream __var_other {
    server 10.0.0.2:1234;
    server 10.0.0.4:1235;
}

server {
    listen 10.3.4.5:8080;
    server_name other.front.example.org;
    location / {
        proxy_pass http://__var_other;
        proxy_set_header    Host $host;
        proxy_set_header    X-Real-IP $remote_addr;
        proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(join(self.tempdir, 'other.frontend.conf')).read())

    def testShouldConfigureGivenAliases(self):
        n = NginxConfig(type='api', nginxConfigDir=self.tempdir, minVersion=VERSION, untilVersion=VERSION_PLUS_ONE)
        mustUpdate, sleeptime = n.updateConfig(
            services={
                newId(): {'type':'other', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'api', 'ipAddress':'10.0.0.3', 'infoport':2345, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
            },
            config={
                'api.frontend': {
                    'ipAddress': '10.3.4.5',
                    'port': 80,
                    'fqdn': 'api.front.example.org',
                    'aliases': [
                        'the.api.example.org',
                        '*.api.example.org',
                    ],
                }
            }
        )
        self.assertEquals(True, mustUpdate)
        self.assertTrue(isfile(join(self.tempdir, 'api.frontend.conf')))
        self.assertEquals("""## Generated by zploadbalancer.failover.NginxConfig
upstream __var_api {
    server 10.0.0.3:2345;
}

server {
    listen 10.3.4.5:80;
    server_name api.front.example.org the.api.example.org *.api.example.org;
    location / {
        proxy_pass http://__var_api;
        proxy_set_header    Host $host;
        proxy_set_header    X-Real-IP $remote_addr;
        proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(join(self.tempdir, 'api.frontend.conf')).read())

    def testShouldConfigureErrorPageIfServiceNotAvailable(self):
        n = NginxConfig(type='api', nginxConfigDir=self.tempdir, minVersion=VERSION, untilVersion=VERSION_PLUS_ONE)
        mustUpdate, sleeptime = n.updateConfig(
            services={
                newId(): {'type':'other', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
            },
            config={
                'api.frontend': {
                    'ipAddress': '10.3.4.5',
                    'port': 80,
                    'fqdn': 'api.front.example.org',
                }
            }
        )
        self.assertEquals(True, mustUpdate)
        self.assertTrue(isfile(join(self.tempdir, 'api.frontend.conf')))
        self.assertEqualsWS("""## Generated by zploadbalancer.failover.NginxConfig
server {
    listen 10.3.4.5:80;
    server_name api.front.example.org;
    root %s/failover;  # Note that nginx won't read in a directory for which the root user doesn't have read permissions.
    location / {
        location /unavailable.html {
        }
        return 503;
    }
    error_page 503 /unavailable.html;
}
""" % usrSharePath, open(join(self.tempdir, 'api.frontend.conf')).read())

    def testShouldConfigureErrorPageIfServicesNotReadable(self):
        n = NginxConfig(type='api', nginxConfigDir=self.tempdir, minVersion=VERSION, untilVersion=VERSION_PLUS_ONE)
        mustUpdate, sleeptime = n.updateConfig(
            services={
                newId(): {'type':'api', 'ipAddress':'10.0.0.3', 'infoport':1235, 'active':True, 'readable': False, 'data':{'VERSION': VERSION}},
            },
            config={
                'api.frontend': {
                    'ipAddress': '10.3.4.5',
                    'port': 80,
                    'fqdn': 'api.front.example.org',
                }
            }
        )
        self.assertEquals(True, mustUpdate)
        self.assertTrue(isfile(join(self.tempdir, 'api.frontend.conf')))
        self.assertEqualsWS("""## Generated by zploadbalancer.failover.NginxConfig
server {
    listen 10.3.4.5:80;
    server_name api.front.example.org;
    root %s/failover;  # Note that nginx won't read in a directory for which the root user doesn't have read permissions.
    location / {
        location /unavailable.html {
        }
        return 503;
    }
    error_page 503 /unavailable.html;
}
""" % usrSharePath, open(join(self.tempdir, 'api.frontend.conf')).read())

    def testShouldConfigureServicesWithCorrectVersion(self):
        n = NginxConfig(type='other', nginxConfigDir=self.tempdir, minVersion='0.42', untilVersion='0.43')
        mustUpdate, sleeptime = n.updateConfig(
            services={
                newId(): {'type':'other', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'readable': True, 'data':{'VERSION': '0.41.1'}},
                newId(): {'type':'other', 'ipAddress':'10.0.0.4', 'infoport':1235, 'active':True, 'readable': True, 'data':{'VERSION': '0.42'}},
                newId(): {'type':'other', 'ipAddress':'10.0.0.8', 'infoport':1236, 'active':True, 'readable': True, 'data':{'VERSION': '0.42.3'}},
                newId(): {'type':'other', 'ipAddress':'10.0.0.16', 'infoport':1237, 'active':True, 'readable': True, 'data':{'VERSION': '0.43'}},
            },
            config={
                'other.frontend': {
                    'ipAddress': '10.3.4.5',
                    'port': 8080,
                    'fqdn': 'other.front.example.org',
                }
            }
        )
        self.assertEquals(True, mustUpdate)
        self.assertTrue(isfile(join(self.tempdir, 'other.frontend.conf')))
        self.assertEquals("""## Generated by zploadbalancer.failover.NginxConfig
upstream __var_other {
    server 10.0.0.4:1235;
    server 10.0.0.8:1236;
}

server {
    listen 10.3.4.5:8080;
    server_name other.front.example.org;
    location / {
        proxy_pass http://__var_other;
        proxy_set_header    Host $host;
        proxy_set_header    X-Real-IP $remote_addr;
        proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(join(self.tempdir, 'other.frontend.conf')).read())


VERSION = '1.4'
VERSION_PLUS_ONE = '1.5'
