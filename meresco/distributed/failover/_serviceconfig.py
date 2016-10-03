## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2016 Seecr (Seek You Too B.V.) http://seecr.nl
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

class ServiceConfig(object):
    def __init__(self, type, minVersion, untilVersion, path='/', flag=READABLE, endpoint=None, port=None, name=None):
        self._type = type
        self._minVersion = minVersion
        self._untilVersion = untilVersion
        self._path = path
        self._flag = flag
        self._endpoint = endpoint
        self._matchingServices = []
        self._typeConfig = {}
        self._port = 80 if port is None else port
        self._name = self._type if name is None else name
        self._locations = None
        self._zones = None

    def updateConfig(self, config, services, **kwargs):
        select = SelectService(self._minVersion, services=services, untilVersion=self._untilVersion)
        yield select.updateConfig(config=config, services=services, **kwargs)
        for service in select.findServices(type=self._type, flag=self._flag):
            try:
                self._matchingServices.append(service.selectHostAndPort(endpoint=self._endpoint))
            except ValueError:
                pass
        self._typeConfig = config.get('{0}.frontend'.format(self._type), {})
        return
        yield

    def servernames(self):
        if 'fqdn' in self._typeConfig:
            yield self._typeConfig['fqdn']
        for alias in self._typeConfig.get('aliases', []):
            yield alias

    def listenLines(self):
        listenIps = [ip for ip in ([self._typeConfig.get('ipAddress', self._typeConfig.get('ip'))] + self._typeConfig.get('ipAddresses',[])) if ip]
        if not listenIps:
            listenIps.append('0.0.0.0')
        for listenIp in listenIps:
            yield "    listen {0}:{1};\n".format(listenIp, self._port)

    def zones(self):
        if self._zones is None:
            self._throttling()
        yield '\n'.join(self._zones)

    def locations(self):
        if self._locations is None:
            self._throttling()
        yield '\n'.join(self._locations)

    def _throttling(self):
        throttling = self._typeConfig.get('throttling', {})
        if self._path not in throttling:
            throttling[self._path] = {}
        self._locations = []
        self._zones = []
        for location, data in sorted(throttling.items()):
            zone_name = location.replace("/", "")
            locationData = StringIO()
            locationData.write("""    location {location} {{
        proxy_pass http://__var_{name};\n""".format(name=self._name, location=location))
            if 'max_connections_per_ip' in data:
                locationData.write("        limit_conn {name}-{0}-byip {1};\n".format(zone_name, data['max_connections_per_ip'], name=self._name))
                self._zones.append("limit_conn_zone $binary_remote_addr zone={name}-{0}-byip:10m;".format(zone_name, name=self._name))
            if 'max_connections' in data:
                locationData.write("        limit_conn {name}-{0}-total {1};\n".format(zone_name, data['max_connections'], name=self._name))
                self._zones.append("limit_conn_zone $server_name zone={name}-{0}-total:10m;".format(zone_name, name=self._name))
            locationData.write("    }")
            self._locations.append(locationData.getvalue())