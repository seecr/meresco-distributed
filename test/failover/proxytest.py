## begin license ##
#
# Drents Archief beoogt het Drents erfgoed centraal beschikbaar te stellen.
#
# Copyright (C) 2012-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015-2016 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2016 Drents Archief http://www.drentsarchief.nl
#
# This file is part of "Drents Archief"
#
# "Drents Archief" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Drents Archief" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Drents Archief"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from seecr.test import SeecrTestCase, CallTrace

from meresco.distributed.constants import WRITABLE, READWRITE, READABLE, ADMIN_DOWNLOAD_PERIOD_CONFIG_KEY
from meresco.distributed.failover import Proxy, ServiceConfig, UnusedConfig, SslConfig, HttpToHttpsRedirect
from os import stat
from os.path import isfile, join
from uuid import uuid4
from meresco.distributed.utils import usrSharePath
from weightless.core import asList, consume, asString


newId = lambda: str(uuid4())

class ProxyTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.configFile = join(self.tempdir, 'server.conf')
        self.config = Proxy(name='test', nginxConfigFile=self.configFile)

    def testShouldNotWriteNginxConfigFileIfNothingChanged(self):
        services={
            newId(): {'type':'api', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'data':{'VERSION': VERSION}},
        }
        config={
            'api.frontend': {
                'fqdn': 'api.front.example.org',
            }
        }
        configFile = join(self.tempdir, 'api.frontend.conf')
        n1 = Proxy(nginxConfigFile=configFile)
        n1.addObserver(ServiceConfig(
                type='api',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
            ))
        # n1 = Proxy(type='api', nginxConfigDir=self.tempdir,
        mustUpdate, sleeptime = n1.update(services=services, config=config, verbose=False)
        self.assertTrue(mustUpdate)
        self.assertEquals(30, sleeptime)
        self.assertTrue(isfile(join(self.tempdir, 'api.frontend.conf')))
        stats = stat(join(self.tempdir, 'api.frontend.conf'))

        n2 = Proxy(nginxConfigFile=configFile)
        n2.addObserver(ServiceConfig(
                type='api',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
            ))

        mustUpdate, sleeptime = n2.update(config=config, services=services, verbose=False)
        self.assertFalse(mustUpdate)
        self.assertEquals(stats, stat(join(self.tempdir, 'api.frontend.conf')))

    def testBaseOnWritable(self):
        services={
                newId(): {'type':'api', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'readable': True, 'writable': True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'api', 'ipAddress':'10.0.0.3', 'infoport':2345, 'active':True, 'readable': True, 'writable': False, 'data':{'VERSION': VERSION}},
        }
        config={
            'api.frontend': {
                'fqdn': 'api.front.example.org',
                'ipAddress': '1.2.3.4',
            }
        }
        n1 = Proxy(nginxConfigFile=self.configFile)
        n1.addObserver(ServiceConfig(
                type='api',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
                flag=WRITABLE,
                name='name',
            ))

        mustUpdate, sleeptime = n1.update(config=config, services=services, verbose=False)
        self.assertTrue(mustUpdate)
        self.assertEquals(30, sleeptime)
        self.assertTrue(isfile(self.configFile))
        self.assertEqualsWS("""## Generated by meresco.distributed.failover.Proxy
upstream __var_name {
    server 10.0.0.2:1234;
}

server {
    listen 1.2.3.4:80;
    server_name api.front.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;

    location / {
        proxy_pass http://__var_name;
    }

    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(self.configFile).read())

    def testBaseOnBothWritableAndReadable(self):
        services={
                newId(): {'type':'api', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'readable': True, 'writable': True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'api', 'ipAddress':'10.0.0.3', 'infoport':2345, 'active':True, 'readable': True, 'writable': False, 'data':{'VERSION': VERSION}},
                newId(): {'type':'api', 'ipAddress':'10.0.0.4', 'infoport':3456, 'active':True, 'readable': False, 'writable': True, 'data':{'VERSION': VERSION}},
        }
        config={
            'api.frontend': {
                'fqdn': 'api.front.example.org',
                'ipAddress': '1.2.3.4',
            }
        }

        n1 = Proxy(nginxConfigFile=self.configFile)
        n1.addObserver(ServiceConfig(
                type='api',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
                flag=READWRITE,
                name='name',
            ))
        mustUpdate, sleeptime = n1.update(config=config, services=services, verbose=False)
        self.assertTrue(mustUpdate)
        self.assertEquals(30, sleeptime)
        self.assertEqualsWS("""## Generated by meresco.distributed.failover.Proxy
upstream __var_name {
    server 10.0.0.2:1234;
}

server {
    listen 1.2.3.4:80;
    server_name api.front.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;

    location / {
        proxy_pass http://__var_name;
    }

    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(self.configFile).read())

    def testNameCheck(self):
        def name(name):
            return ServiceConfig(type='api', name=name, minVersion=VERSION, untilVersion=VERSION_PLUS_ONE)
        self.assertRaises(ValueError, name, 'api.1.4')
        self.assertRaises(ValueError, name, 'api.1$%_4')

        self.assertTrue(name('api_14'))


    def testShouldConfigureApiServers(self):
        n1 = Proxy(nginxConfigFile=self.configFile, usrSharePath='/tmp/usr/share/failover')
        n1.addObserver(ServiceConfig(
                type='api',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
                flag=READABLE,
                name='name',
            ))
        mustUpdate, sleeptime = n1.update(
            services={
                newId(): {'type':'api', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'api', 'ipAddress':'10.0.0.3', 'infoport':2345, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'plein', 'ipAddress':'10.0.0.4', 'infoport':2346, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
            },
            config={
                'api.frontend': {
                    'fqdn': 'api.front.example.org',
                }
            },
            verbose=False
        )
        self.assertEquals(True, mustUpdate)
        self.assertEqualText("""## Generated by meresco.distributed.failover.Proxy

upstream __var_name {
    server 10.0.0.2:1234;
    server 10.0.0.3:2345;
}

server {
    listen 0.0.0.0:80;
    server_name api.front.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;

    location / {
        proxy_pass http://__var_name;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root /tmp/usr/share/failover;
    }
    client_max_body_size 0;
}
""", open(self.configFile).read())

    def testHttpToHttps(self):
        n1 = HttpToHttpsRedirect(nginxConfigFile=self.configFile, usrSharePath='/tmp/usr/share/failover')
        n1.addObserver(ServiceConfig(
                type='api',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
                flag=READABLE,
                name='name',
            ))
        mustUpdate, sleeptime = n1.update(
            services={
                newId(): {'type':'api', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'api', 'ipAddress':'10.0.0.3', 'infoport':2345, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'plein', 'ipAddress':'10.0.0.4', 'infoport':2346, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
            },
            config={
                'api.frontend': {
                    'fqdn': 'api.front.example.org',
                    'aliases': ['alias1', 'alias2'],
                    'ipAddresses': ['10.0.0.1', '10.0.0.2']
                }
            },
            verbose=False
        )
        self.assertEquals(True, mustUpdate)
        self.assertEqualText("""## Generated by meresco.distributed.failover.HttpToHttpsRedirect

server {
    listen 10.0.0.1:80;
    listen 10.0.0.2:80;
    server_name api.front.example.org alias1 alias2;

    rewrite  ^ https://api.front.example.org$request_uri? permanent;
}
""", open(self.configFile).read())

    def testShouldConfigureAnyGivenTypeOfServiceWithPort(self):
        n1 = Proxy(nginxConfigFile=self.configFile)
        n1.addObserver(ServiceConfig(
                type='other',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
                flag=READABLE,
                port=8080,
            ))
        mustUpdate, sleeptime = n1.update(
            services={
                newId(): {'type':'other', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'other', 'ipAddress':'10.0.0.4', 'infoport':1235, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'other', 'ipAddress':'10.0.0.5', 'infoport':1236, 'active':True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'api', 'ipAddress':'10.0.0.3', 'infoport':2345, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
            },
            config={
                'other.frontend': {
                    'fqdn': 'other.front.example.org',
                }
            },
            verbose=False
        )
        self.assertEquals(True, mustUpdate)
        self.assertEqualText("""## Generated by meresco.distributed.failover.Proxy

upstream __var_other {
    server 10.0.0.2:1234;
    server 10.0.0.4:1235;
}

server {
    listen 0.0.0.0:8080;
    server_name other.front.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;

    location / {
        proxy_pass http://__var_other;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(self.configFile).read())

    def testShouldConfigureGivenAliases(self):
        n1 = Proxy(nginxConfigFile=self.configFile)
        n1.addObserver(ServiceConfig(
                type='api',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
                flag=READABLE,
            ))
        mustUpdate, sleeptime = n1.update(
            services={
                newId(): {'type':'other', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
                newId(): {'type':'api', 'ipAddress':'10.0.0.3', 'infoport':2345, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
            },
            config={
                'api.frontend': {
                    'port': 80,
                    'fqdn': 'api.front.example.org',
                    'aliases': [
                        'the.api.example.org',
                        '*.api.example.org',
                    ],
                }
            },
            verbose=False
        )
        self.assertEquals(True, mustUpdate)
        self.assertEqualText("""## Generated by meresco.distributed.failover.Proxy

upstream __var_api {
    server 10.0.0.3:2345;
}

server {
    listen 0.0.0.0:80;
    server_name api.front.example.org the.api.example.org *.api.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;

    location / {
        proxy_pass http://__var_api;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(self.configFile).read())

    def testShouldConfigureErrorPageIfServiceNotAvailable(self):
        n1 = Proxy(nginxConfigFile=self.configFile)
        n1.addObserver(ServiceConfig(
                type='api',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
                flag=READABLE,
            ))
        mustUpdate, sleeptime = n1.update(
            services={
                newId(): {'type':'other', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
            },
            config={
                'api.frontend': {
                    'port': 80,
                    'fqdn': 'api.front.example.org',
                }
            },
            verbose=False
        )
        self.assertEquals(True, mustUpdate)
        self.assertEqualText("""## Generated by meresco.distributed.failover.Proxy


server {
    listen 0.0.0.0:80;
    server_name api.front.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;

    location / {
        location /unavailable.html {
        }
        return 503;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(self.configFile).read())

    def testShouldConfigureErrorPageIfServicesNotReadable(self):
        n1 = Proxy(nginxConfigFile=self.configFile)
        n1.addObserver(ServiceConfig(
                type='api',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
                flag=READABLE,
            ))
        mustUpdate, sleeptime = n1.update(
            services={
                newId(): {'type':'api', 'ipAddress':'10.0.0.3', 'infoport':1235, 'active':True, 'readable': False, 'data':{'VERSION': VERSION}},
            },
            config={
                'api.frontend': {
                    'port': 80,
                    'fqdn': 'api.front.example.org',
                }
            },
            verbose=False
        )
        self.assertEquals(True, mustUpdate)
        self.assertEqualText("""## Generated by meresco.distributed.failover.Proxy


server {
    listen 0.0.0.0:80;
    server_name api.front.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;

    location / {
        location /unavailable.html {
        }
        return 503;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(self.configFile).read())

    def testShouldConfigureServicesWithCorrectVersion(self):
        n1 = Proxy(nginxConfigFile=self.configFile)
        n1.addObserver(ServiceConfig(
                type='other',
                minVersion='0.42',
                untilVersion='0.43',
                flag=READABLE,
                port=8080,
            ))
        mustUpdate, sleeptime = n1.update(
            services={
                newId(): {'type':'other', 'ipAddress':'10.0.0.2', 'infoport':1234, 'active':True, 'readable': True, 'data':{'VERSION': '0.41.1'}},
                newId(): {'type':'other', 'ipAddress':'10.0.0.4', 'infoport':1235, 'active':True, 'readable': True, 'data':{'VERSION': '0.42'}},
                newId(): {'type':'other', 'ipAddress':'10.0.0.8', 'infoport':1236, 'active':True, 'readable': True, 'data':{'VERSION': '0.42.3'}},
                newId(): {'type':'other', 'ipAddress':'10.0.0.16', 'infoport':1237, 'active':True, 'readable': True, 'data':{'VERSION': '0.43'}},
            },
            config={
                'other.frontend': {
                    'fqdn': 'other.front.example.org',
                }
            },
            verbose=False
        )
        self.assertEquals(True, mustUpdate)
        self.assertEqualText("""## Generated by meresco.distributed.failover.Proxy

upstream __var_other {
    server 10.0.0.4:1235;
    server 10.0.0.8:1236;
}

server {
    listen 0.0.0.0:8080;
    server_name other.front.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;

    location / {
        proxy_pass http://__var_other;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(self.configFile).read())

    def testShouldConfigureUnusedPage(self):
        n1 = Proxy(nginxConfigFile=self.configFile)
        n1.addObserver(UnusedConfig(
                servername='api.front.example.org'
            ))
        mustUpdate, sleeptime = n1.update(
            services={
            },
            config={
            },
            verbose=False,
        )
        self.assertEquals(True, mustUpdate)
        self.assertEqualText('''## Generated by meresco.distributed.failover.Proxy


server {
    listen 0.0.0.0:80;
    server_name api.front.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;

    location / {
        root %(path)s/failover;
        location /unused.html {
        }
        return 410;
    }
    error_page 410 /unused.html;
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %(path)s/failover;
    }
    client_max_body_size 0;
}
''' % dict(path=usrSharePath), open(self.configFile).read())


    def testShouldConfigureThrottling(self):
        n1 = Proxy(nginxConfigFile=self.configFile)
        n1.addObserver(ServiceConfig(
                type='api',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
                flag=READABLE,
                name='api_18',
            ))
        mustUpdate, sleeptime = n1.update(
            services={
                newId(): {'type':'api', 'ipAddress':'10.0.0.3', 'infoport':1235, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
            },
            config={
                'api.frontend': {
                    'port': 80,
                    'fqdn': 'api.front.example.org',
                    'throttling': {
                        '/sru': {
                            'max_connections': 10,
                            'max_connections_per_ip': 5
                        },
                        '/sru/holding': {}
                    }
                }
            },
            verbose=False,
        )
        self.assertEquals(True, mustUpdate)
        self.assertEqualText("""## Generated by meresco.distributed.failover.Proxy

upstream __var_api_18 {
    server 10.0.0.3:1235;
}
limit_conn_zone $binary_remote_addr zone=api_18-sru-byip:10m;
limit_conn_zone $server_name zone=api_18-sru-total:10m;
server {
    listen 0.0.0.0:80;
    server_name api.front.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;

    location / {
        proxy_pass http://__var_api_18;
    }
    location /sru {
        proxy_pass http://__var_api_18;
        limit_conn api_18-sru-byip 5;
        limit_conn api_18-sru-total 10;
    }
    location /sru/holding {
        proxy_pass http://__var_api_18;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(self.configFile).read())

    def testUseAdminDownloadPeriod(self):
        config={
            'api.frontend': {
                'fqdn': 'api.front.example.org',
            },
            ADMIN_DOWNLOAD_PERIOD_CONFIG_KEY: 5
        }
        n1 = Proxy(nginxConfigFile=self.configFile)
        n1.addObserver(UnusedConfig(servername='my.example.org'))
        mustUpdate, sleeptime = n1.update(config=config, services={}, verbose=False)
        self.assertEquals(5, sleeptime)

    def testListenIps(self):
        n1 = Proxy(nginxConfigFile=self.configFile)
        n1.addObserver(ServiceConfig(
                type='api',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
                flag=READABLE,
            ))
        mustUpdate, sleeptime = n1.update(
            services={},
            config={
                'api.frontend': {
                    'port': 80,
                    'fqdn': 'api.front.example.org',
                    'ipAddress': '1.2.3.4',
                    'ipAddresses': ['2.3.4.5']
                }
            },
            verbose=False
        )
        self.assertEquals(True, mustUpdate)
        self.assertTrue(isfile(self.configFile))
        self.assertEqualText("""## Generated by meresco.distributed.failover.Proxy


server {
    listen 1.2.3.4:80;
    listen 2.3.4.5:80;
    server_name api.front.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;

    location / {
        location /unavailable.html {
        }
        return 503;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(self.configFile).read())

    def testSslNoServices(self):
        n1 = Proxy(nginxConfigFile=self.configFile)
        n1.addObserver(ServiceConfig(
                type='api',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
                flag=READABLE,
                port=443,
            ))
        n1.addObserver(SslConfig(certificate='/path/to/server.crt', key='/path/to/server.pem'))
        mustUpdate, sleeptime = n1.update(
            services={},
            config={
                'api.frontend': {
                    'port': 443,
                    'fqdn': 'api.front.example.org',
                    'ipAddress': '1.2.3.4',
                }
            },
            verbose=False,
       )
        self.assertEquals(True, mustUpdate)
        self.assertTrue(isfile(self.configFile))
        self.assertEqualText("""## Generated by meresco.distributed.failover.Proxy


server {
    listen 1.2.3.4:443;
    server_name api.front.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;


    ssl on;

    ssl_certificate         /path/to/server.crt;
    ssl_certificate_key     /path/to/server.pem;
    ssl_protocols           TLSv1 TLSv1.1 TLSv1.2;
    keepalive_timeout       60;
    ssl_session_cache       shared:SSL:10m;

    location / {
        location /unavailable.html {
        }
        return 503;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(self.configFile).read())

    def testSsl(self):
        n1 = Proxy(nginxConfigFile=self.configFile)
        n1.addObserver(ServiceConfig(
                type='api',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
                flag=READABLE,
                port=443,
            ))
        n1.addObserver(SslConfig(certificate='/path/to/server.crt', key='/path/to/server.pem'))
        mustUpdate, sleeptime = n1.update(
            services={
                newId(): {'type':'api', 'ipAddress':'10.0.0.3', 'infoport':1235, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}},
            },
            config={
                'api.frontend': {
                    'port': 443,
                    'fqdn': 'api.front.example.org',
                    'ipAddress': '1.2.3.4',
                }
            },
            verbose=False,
        )
        self.assertEquals(True, mustUpdate)
        self.assertTrue(isfile(self.configFile))
        self.assertEqualText("""## Generated by meresco.distributed.failover.Proxy

upstream __var_api {
    server 10.0.0.3:1235;
}

server {
    listen 1.2.3.4:443;
    server_name api.front.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;


    ssl on;

    ssl_certificate         /path/to/server.crt;
    ssl_certificate_key     /path/to/server.pem;
    ssl_protocols           TLSv1 TLSv1.1 TLSv1.2;
    keepalive_timeout       60;
    ssl_session_cache       shared:SSL:10m;

    location / {
        proxy_pass http://__var_api;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(self.configFile).read())

    def testEndpointPortForListen(self):
        n1 = Proxy(nginxConfigFile=self.configFile)
        n1.addObserver(ServiceConfig(
                type='api',
                minVersion=VERSION,
                untilVersion=VERSION_PLUS_ONE,
                flag=READABLE,
                endpoint='web',
            ))
        def endpoints(nr):
            result = {
                'index': "http://10.12.14.16:50000/",
            }
            result['web'] = "http://10.11.12.{0}:{1}/".format(13+nr, 54321+nr)
            return result
        mustUpdate, sleeptime = n1.update(
            services={
                newId(): {'type':'api', 'ipAddress':'10.0.0.3', 'infoport':1235, 'active':True, 'readable': True, 'data':{'VERSION': VERSION, 'endpoints': endpoints(0)}},
                newId(): {'type':'api', 'ipAddress':'10.0.0.4', 'infoport':1236, 'active':True, 'readable': True, 'data':{'VERSION': VERSION, 'endpoints': endpoints(1)}},
                newId(): {'type':'api', 'ipAddress':'10.0.0.5', 'infoport':1237, 'active':True, 'readable': True, 'data':{'VERSION': VERSION}, 'identifier':'dezeniet'},
            },
            config={
                'api.frontend': {
                    'port': 443,
                    'fqdn': 'api.front.example.org',
                    'ipAddress': '1.2.3.4',
                }
            },
            verbose=False
        )
        self.assertEquals(True, mustUpdate)
        self.assertTrue(isfile(self.configFile))
        self.assertEqualText("""## Generated by meresco.distributed.failover.Proxy

upstream __var_api {
    server 10.11.12.13:54321;
    server 10.11.12.14:54322;
}

server {
    listen 1.2.3.4:80;
    server_name api.front.example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;

    location / {
        proxy_pass http://__var_api;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}
""" % usrSharePath, open(self.configFile).read())

    def testEmpty(self):
        observer = CallTrace(methods=dict(servernames=lambda:(f for f in ['example.org'])), emptyGeneratorMethods=['sslLines', 'matchingServices', 'zones', 'listenLines', 'locations', 'updateConfig'])
        self.config.addObserver(observer)
        result = self.config.generate(config={'some':'thing'}, services={'services':[]})
        self.assertEqualsWS('''## Generated by meresco.distributed.failover.Proxy

server {
    server_name example.org;

    proxy_set_header    Host $host;
    proxy_set_header    X-Real-IP $remote_addr;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;

    location / {
        location /unavailable.html {
        }
        return 503;
    }

    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s/failover;
    }
    client_max_body_size 0;
}''' % usrSharePath, result)
        self.assertEquals([
                'updateConfig',
                'matchingServices',
                'zones',
                'listenLines',
                'servernames',
                'sslLines',
                'locations',
            ], observer.calledMethodNames())
        self.assertEqual(dict(config={'some':'thing'}, services={'services':[]}), observer.calledMethods[0].kwargs)
        self.assertEqual((), observer.calledMethods[0].args)
        for m in observer.calledMethods[1:]:
            self.assertEqual(dict(), m.kwargs)
            self.assertEqual((), m.args)

    def testNoServernamesMeansError(self):
        self.assertRaises(ValueError, lambda:self.config.generate())

    def testUpdateConfig(self):
        self.config.generate = lambda **kwargs: 'config'
        result = self.config.update(config={}, services={}, verbose=False)
        self.assertEqual((True, 30), (result.mustUpdate, result.sleeptime))
        result = self.config.update(config={}, services={}, verbose=False)
        self.assertEqual((False, 30), result)
        self.config.generate = lambda **kwargs: 'config2'
        result = self.config.update(config={}, services={}, verbose=False)
        self.assertEqual((True, 30), result)
        self.assertEqual('config2', open(join(self.tempdir, 'server.conf')).read())

    def testSslConfig(self):
        c = SslConfig(certificate='/path/to/ssl.crt', key='/path/to/ssl.pem')
        self.assertEqual('''
    ssl on;

    ssl_certificate         /path/to/ssl.crt;
    ssl_certificate_key     /path/to/ssl.pem;
    ssl_protocols           TLSv1 TLSv1.1 TLSv1.2;
    keepalive_timeout       60;
    ssl_session_cache       shared:SSL:10m;

''', asString(c.sslLines()))

    def testServiceConfig(self):
        c = ServiceConfig(type='api', minVersion="4.2", untilVersion="5.0")
        consume(c.updateConfig(**CONFIG_SERVICES()))
        self.assertEquals(['api.front.example.org', 'alias1', 'alias2'], asList(c.servernames()))
        self.assertEquals('', asString(c.zones()))
        self.assertEquals('    location / {\n        proxy_pass http://__var_api;\n    }', asString(c.locations()))
        self.assertEquals('    listen 0.0.0.0:80;\n', asString(c.listenLines()))

    def testServiceConfigThrottling(self):
        c = ServiceConfig(type='api', minVersion="4.2", untilVersion="5.0", path='/main')
        configServices = CONFIG_SERVICES()
        configServices['config']['api.frontend']['throttling'] = {
            '/path': {'max_connections_per_ip' : 10, 'max_connections': 100},
            '/other': {'max_connections_per_ip' : 30, 'max_connections': 150}
        }
        consume(c.updateConfig(**configServices))
        self.assertEquals([
            'limit_conn_zone $binary_remote_addr zone=api-other-byip:10m;',
            'limit_conn_zone $server_name zone=api-other-total:10m;',
            'limit_conn_zone $binary_remote_addr zone=api-path-byip:10m;',
            'limit_conn_zone $server_name zone=api-path-total:10m;'
            ], asString(c.zones()).split('\n'))
        self.assertEquals([
            '    location /main {',
            '        proxy_pass http://__var_api;',
            '    }',
            '    location /other {',
            '        proxy_pass http://__var_api;',
            '        limit_conn api-other-byip 30;',
            '        limit_conn api-other-total 150;',
            '    }',
            '    location /path {',
            '        proxy_pass http://__var_api;',
            '        limit_conn api-path-byip 10;',
            '        limit_conn api-path-total 100;',
            '    }',
            ], asString(c.locations()).split('\n'))

    def testServiceConfigListen(self):
        c = ServiceConfig(type='api', minVersion="4.2", untilVersion="5.0", path='/main', port=443)
        configServices = CONFIG_SERVICES()
        configServices['config']['api.frontend']['ipAddress'] = '10.0.0.1'
        configServices['config']['api.frontend']['ipAddresses'] = ['10.0.0.2', '10.0.0.3']
        consume(c.updateConfig(**configServices))
        self.assertEquals('    listen 10.0.0.1:443;\n    listen 10.0.0.2:443;\n    listen 10.0.0.3:443;\n', asString(c.listenLines()))

    def testNotAvailable(self):
        c = ServiceConfig(type='web', minVersion="4.2", untilVersion="5.0", path='/main', port=443)
        consume(c.updateConfig(**CONFIG_SERVICES()))
        self.assertEqual([
            '    location /main {',
            '        location /unavailable.html {',
            '        }',
            '        return 503;',
            '    }'
            ], asString(c.locations()).split('\n'))

    def testMatchingServices(self):
        c = ServiceConfig(type='api', minVersion="4.2", untilVersion="5.0", path='/main', port=443)
        consume(c.updateConfig(**CONFIG_SERVICES()))
        self.assertEqual([
                'upstream __var_api {',
                '    server 10.0.0.2:1234;',
                '}',
                ''
            ], asString(c.matchingServices()).split('\n'))

    def testMultipleListenLines(self):
        self.maxDiff = None
        p = Proxy(nginxConfigFile=self.configFile)
        p.addObserver(ServiceConfig(type='api', minVersion="4.2", untilVersion="5.0", path='/other', port=443))
        p.addObserver(ServiceConfig(type='api', minVersion="4.2", untilVersion="5.0", path='/main', port=443))
        self.assertEqual([
            '## Generated by meresco.distributed.failover.Proxy',
            '',
            'upstream __var_api {',
            '    server 10.0.0.2:1234;',
            '}',
            'upstream __var_api {',
            '    server 10.0.0.2:1234;',
            '}',
            '',
            'server {',
            '    listen 0.0.0.0:443;',
            '    server_name api.front.example.org alias1 alias2 api.front.example.org alias1 alias2;',
            '',
            '    proxy_set_header    Host $host;',
            '    proxy_set_header    X-Real-IP $remote_addr;',
            '    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;',
            '',
            '    location /other {',
            '        proxy_pass http://__var_api;',
            '    }',
            '    location /main {',
            '        proxy_pass http://__var_api;',
            '    }',
            '    error_page 500 502 503 504 =503 /unavailable.html;',
            '    location /unavailable.html {',
            '        root %s/failover;' % usrSharePath,
            '    }',
            '    client_max_body_size 0;',
            '}',
            ''
            ], p.generate(**CONFIG_SERVICES()).split('\n'))


def CONFIG_SERVICES():
    return dict(
        services={
            newId(): {'type':'api', 'ipAddress':'10.0.0.2', 'infoport':1234, 'readable':True, 'data':{'VERSION': "4.3"}},
        },
        config={
            'api.frontend': {
                'fqdn': 'api.front.example.org',
                'aliases': ['alias1', 'alias2']
            }
        })


newId = lambda: str(uuid4())

VERSION = '1.4'
VERSION_PLUS_ONE = '1.5'
