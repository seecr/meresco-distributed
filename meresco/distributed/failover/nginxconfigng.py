## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2016 SURFmarket https://surf.nl
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

from weightless.core import asList, asString
from meresco.core import Observable
from meresco.distributed.utils import usrSharePath as defaultUsrSharePath
from os.path import join

class NginxConfigNG(Observable):
    def __init__(self, usrSharePath=None, **kwargs):
        Observable.__init__(self, **kwargs)
        self._usrSharePath = join(defaultUsrSharePath, 'failover') if usrSharePath is None else usrSharePath

    def generate(self, **kwargs):
        return asString(self._generate(**kwargs))

    def _generate(self, **kwargs):
        yield '## Generated by NginxConfig \n\n'
        yield self.all.matchingServices()
        yield self.all.zones()
        yield '\nserver {\n'
        yield self.all.listenLines()
        yield '    server_name '
        yield ' '.join(asList(self.all.servernames()))
        yield ';\n\n'
        yield self.proxy_settings
        yield self.all.sslLines()
        locations = asString(self.all.locations())
        if not locations:
            yield self._allLocationsUnavailable()
        yield self._unavailable()
        yield '}\n'


    proxy_settings = '    proxy_set_header    Host $host;\n    proxy_set_header    X-Real-IP $remote_addr;\n    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;\n\n'

    def _unavailable(self):
        return '''    error_page 500 502 503 504 =503 /unavailable.html;
    location /unavailable.html {
        root %s;
    }
    client_max_body_size 0;
''' % self._usrSharePath

    def _allLocationsUnavailable(self):
        return '''
    location / {
        location /unavailable.html {
        }
        return 503;
    }
'''