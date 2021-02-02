## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2016, 2018 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2018 Stichting Kennisnet https://www.kennisnet.nl
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

import sys
from netaddr import IPAddress
from collections import namedtuple
from itertools import chain

def log(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()

def noLog(msg):
    pass

def formatIp(ipAddress):
    ip = IPAddress(ipAddress)
    if ip.version == 6:
        return '[%s]' % ip.format()
    return ip.format()

def create_path(path, paths):
    if path and paths:
        raise TypeError("Use either path or paths")
    if paths:
        return '~ ^({})'.format('|'.join(paths))
    return path or '/'

def listenIps(config):
    return [ip for ip in ([config.get('ipAddress', config.get('ip'))] + config.get('ipAddresses',[])) if ip]

def servernames(config):
    return [f for f in chain([config.get('fqdn')], config.get('aliases', [])) if f]

UpdateResult = namedtuple('UpdateResult', ['mustUpdate', 'sleeptime'])

__all__ = ['formatIp', 'UpdateResult', 'listenIps', 'servernames']
