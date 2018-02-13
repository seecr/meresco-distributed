## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2016-2018 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2018 SURF https://surf.nl
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

from StringIO import StringIO
from meresco.distributed import SelectService
from meresco.distributed.constants import READABLE
from ._utils import log, noLog, formatIp
from hashlib import md5
import re

class ServiceConfig(object):
    def __init__(self, type, minVersion, untilVersion, path=None, paths=None, flag=READABLE, endpoint=None, port=None, name=None):
        self._minVersion = minVersion
        self._untilVersion = untilVersion
        self._typeConfig = {}
        self._globalConfig = {}
        self._port = 80 if port is None else port
        self._type = type
        self._path = _create_path(path, paths)
        self._flag = flag
        self._endpoint = endpoint
        self._matchingServices = []
        self._name = self._type if name is None else name
        namecheck(self._name)
        self._locations = None
        self._zones = None
        self._log = noLog

    def updateConfig(self, config, services, **kwargs):
        self._typeConfig = config.get('{0}.frontend'.format(self._type), {})
        self._globalConfig = config.get('global.frontend', {})
        if kwargs.get('verbose', False):
            self._log = log
        select = SelectService(self._minVersion, services=services, untilVersion=self._untilVersion)
        yield select.updateConfig(config=config, services=services, **kwargs)
        for service in select.findServices(type=self._type, flag=self._flag):
            try:
                self._matchingServices.append(service.selectHostAndPort(endpoint=self._endpoint))
            except ValueError:
                pass

    def zones(self):
        if self._zones is None:
            self._throttling()
        yield '\n'.join(self._zones)

    def locations(self):
        if self._locations is None:
            self._throttling()
        yield '\n'.join(self._locations)

    def servernames(self):
        if 'fqdn' in self._typeConfig:
            yield self._typeConfig['fqdn']
        for alias in self._typeConfig.get('aliases', []):
            yield alias

    def listenLines(self):
        listenIps = _listenIps(self._typeConfig) or _listenIps(self._globalConfig)
        if not listenIps:
            listenIps.append('0.0.0.0')
        for listenIp in listenIps:
            yield "    listen {0}:{1};\n".format(formatIp(listenIp), self._port)

    def _varname(self):
        return '__var_{0}_{1}'.format(md5(''.join(self.servernames())).hexdigest(), self._name)

    def matchingServices(self):
        if self._matchingServices:
            servers = ['    server {0}:{1};'.format(*s) for s in sorted(self._matchingServices)]
            yield 'upstream {0} {{\n{1}\n}}\n'.format(self._varname(), '\n'.join(servers))
            self._log(''.join('Service {name} at {0}:{1}\n'.format(host, port, name=self._name) for host, port in self._matchingServices))

    def _throttling(self):
        throttling = self._typeConfig.get('throttling', {})
        if self._path not in throttling:
            throttling[self._path] = {}
        self._locations = []
        self._zones = []
        if not self._matchingServices:
            if self._path == '/':
                self._locations.append('''    location {0} {{
        location /unavailable.html {{
        }}
        return 503;
    }}'''.format(self._path))
            else:
                self._locations.append('''    location {0} {{
        return 503;
    }}'''.format(self._path))

            return
        for location, data in sorted(throttling.items()):
            zone_name = location.replace("/", "")
            locationData = StringIO()
            locationData.write("""    location {location} {{
        proxy_pass http://{varname};\n""".format(varname=self._varname(), location=location))
            if 'max_connections_per_ip' in data:
                locationData.write("        limit_conn {name}-{0}-byip {1};\n".format(zone_name, data['max_connections_per_ip'], name=self._name))
                self._zones.append("limit_conn_zone $binary_remote_addr zone={name}-{0}-byip:10m;".format(zone_name, name=self._name))
            if 'max_connections' in data:
                locationData.write("        limit_conn {name}-{0}-total {1};\n".format(zone_name, data['max_connections'], name=self._name))
                self._zones.append("limit_conn_zone $server_name zone={name}-{0}-total:10m;".format(zone_name, name=self._name))
            locationData.write("    }")
            self._locations.append(locationData.getvalue())

NAME_RE = re.compile(r'^\w+$')
def namecheck(name):
    if not NAME_RE.match(name):
        raise ValueError('Only alphanumeric characters allowed.')

def _create_path(path, paths):
    if path and paths:
        raise TypeError("Use either path or paths")
    if paths:
        return '~ ^({})'.format('|'.join(paths))
    return path or '/'

def _listenIps(config):
    return [ip for ip in ([config.get('ipAddress', config.get('ip'))] + config.get('ipAddresses',[])) if ip]

