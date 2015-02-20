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

from os.path import isfile, join
from os import rename
from StringIO import StringIO
from time import sleep
from sys import stdout

from zploadbalancer.failover.utils import usrSharePath
from seecr.utils import Version
from re import compile


class NginxConfig(object):
    def __init__(self, type, nginxConfigDir, minVersion, untilVersion, verbose=False, name=None, **kwargs):
        assert type.strip() != '', "Expected a type name."
        self._type = type
        self._name = self._type if name is None else name
        namecheck(self._name)
        self._nginxConfigFile = join(nginxConfigDir, '%s.frontend.conf' % self._name)
        self._verbose = verbose
        self._minVersion = Version(minVersion)
        self._untilVersion = Version(untilVersion)

    def updateConfig(self, config, services, **ignored):
        typeConfig = config['%s.frontend' % self._type]
        sleeptime = typeConfig.get('reconfiguration.interval', 30)
        mustUpdate = self._updateConfig(services, typeConfig)
        self._log("Sleeping: %ss\n" % sleeptime)
        return mustUpdate, sleeptime

    def _updateConfig(self, services, typeConfig):
        matchingServices = self._selectHostAndPort(services)
        serverName = typeConfig['fqdn']
        aliases = ' '.join(typeConfig.get('aliases', []))
        if aliases:
            serverName += ' %s' % aliases
        listenPort = typeConfig.get('port', 80)
        conf = StringIO()
        conf.write("## Generated by zploadbalancer.failover.NginxConfig\n")
        if len(matchingServices) > 0:
            conf.write("""upstream __var_%s {\n""" % self._name)
            for host, port in sorted(matchingServices):
                conf.write("    server {host}:{port};\n".format(host=host, port=port))
                self._log("Service {type} at {host}:{port}\n".format(host=host, port=port, type=self._type))
            conf.write("""}

server {
    listen 0.0.0.0:%(listenPort)s;
    server_name %(serverName)s;
    location / {
        proxy_pass http://__var_%%s;
        proxy_set_header    Host $host;
        proxy_set_header    X-Real-IP $remote_addr;
        proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %%s;
    }
    client_max_body_size 0;
}\n""" % locals() % (self._name, join(usrSharePath, 'failover')))
        else:
            conf.write("""
server {
    listen 0.0.0.0:%(listenPort)s;
    server_name %(serverName)s;
    root %%s;  # Note that nginx won't read in a directory for which the root user doesn't have read permissions.
    location / {
        location /unavailable.html {
        }
        return 503;
    }
    error_page 503 /unavailable.html;
}\n""" % locals() % (join(usrSharePath, 'failover')))

        if not isfile(self._nginxConfigFile) or conf.getvalue() != open(self._nginxConfigFile).read():
            with open(self._nginxConfigFile+'~', 'w') as fd:
                fd.write(conf.getvalue())
            rename(self._nginxConfigFile+'~', self._nginxConfigFile)
            return True
        return False

    def _sleep(self, sleeptime):
        sleep(sleeptime)

    def _log(self, msg):
        if not self._verbose:
            return
        stdout.write(msg)
        stdout.flush()

    def _selectHostAndPort(self, services):
        matchingServices = []
        for serviceIdentifier, service in services.items():
            if not service.get('readable', False):
                continue
            if service['type'] == self._type:
                if self._minVersion <= Version(service['data']['VERSION']) < self._untilVersion:
                    matchingServices.append((service['ipAddress'], service['infoport']))
        return matchingServices

NAME_RE = compile(r'^\w+$')
def namecheck(name):
    if not NAME_RE.match(name):
        raise ValueError('Only alphanumeric characters allowed.')
