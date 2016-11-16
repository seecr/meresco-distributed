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


from os.path import join
from meresco.distributed.utils import usrSharePath as defaultUsrSharePath
from ._utils import formatIp

class UnusedConfig(object):
    def __init__(self, servername, listenIps=None, port=None, usrSharePath=None):
        self._usrSharePath = join(defaultUsrSharePath, 'failover') if usrSharePath is None else usrSharePath
        port = 80 if port is None else port
        listenIps = ['0.0.0.0'] if listenIps is None else listenIps
        self._listenLines = '\n'.join("    listen {0}:{1};".format(formatIp(ip), port) for ip in listenIps) + '\n'
        self._servername = servername

    def servernames(self):
        yield self._servername

    def listenLines(self):
        yield self._listenLines

    def locations(self):
        yield """    location / {
        root %s;
        location /unused.html {
        }
        return 410;
    }
    error_page 410 /unused.html;""" % self._usrSharePath