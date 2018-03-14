## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2016, 2018 Seecr (Seek You Too B.V.) http://seecr.nl
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

from ._utils import create_path

class StaticPathConfig(object):
    def __init__(self, path, config):
        self._path = path
        self._config = config

    def locations(self):
        yield '    location {0} {{\n{1}\n    }}\n'.format(self._path, self._config)

class StaticLocations(object):
    def __init__(self, config):
        self._config = config

    def locations(self):
        yield self._config

class StaticServiceConfig(object):
    def __init__(self, remoteIp, remotePort=None, remotePath=None, path=None, paths=None, proxyHeaders=None):
        self._remotePort = remotePort or 80
        self._remoteIp = remoteIp
        self._remotePath = remotePath or ''
        self._path = create_path(path, paths)
        self._proxyHeaders = proxyHeaders or {}

    def locations(self):
        yield """    location {location} {{
        proxy_pass http://{remoteIp}:{remotePort}{remotePath};""".format(location=self._path, remoteIp=self._remoteIp, remotePort=self._remotePort, remotePath=self._remotePath)
        for key, value in self._proxyHeaders.items():
            yield """        proxy_set_header    {key} {value};""".format(key=key, value=value)
        yield """    }"""

class StaticServerName(object):
    def __init__(self, *names):
        self._names = names

    def servernames(self):
        for n in self._names:
            yield n

class StaticListenLine(object):
    def __init__(self, port=None, ip=None):
        self._port = 80 if port is None else port
        self._ip = '0.0.0.0' if ip is None else ip

    def listenLines(self):
        yield "    listen {0}:{1};\n".format(self._ip, self._port)

