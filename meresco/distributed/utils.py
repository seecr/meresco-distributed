## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2015 Stichting Kennisnet http://www.kennisnet.nl
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

from hashlib import sha1
from socket import gethostname, gethostbyname
from os.path import dirname, abspath, join

usrSharePath = '/usr/share/meresco-distributed'
mydir = dirname(abspath(__file__))                  #DO_NOT_DISTRIBUTE
usrSharePath = join(dirname(mydir), "usr-share")    #DO_NOT_DISTRIBUTE

def serviceUpdateHash(secret, **kwargs):
    hashString = secret + ''.join(str(value) for key, value in sorted(kwargs.items()))
    return sha1(hashString).hexdigest()

IP_ADDRESS = gethostbyname(gethostname())

def ipsAndRanges(ipSpecs, includeLocalhost=True, knownIps=None):
    '''parses (json) dictionary config format into something IpFilter / Deproxy's updateIps-method understands.'''
    knownIps = {} if knownIps is None else knownIps
    ips = set()
    for ipItem in ipSpecs:
        if 'known' in ipItem:
            ips.update(knownIps.get(ipItem['known'], set()))
    ips.update(ipItem['ip'] for ipItem in ipSpecs if 'ip' in ipItem)
    ips.update(ipItem['ipAddress'] for ipItem in ipSpecs if 'ipAddress' in ipItem)  # *.frontend ip's
    if includeLocalhost:
        ips.add('127.0.0.1')
    ipRanges = set(
        (ipItem['start'], ipItem['end'])
        for ipItem in ipSpecs
        if 'start' in ipItem and 'end' in ipItem
    )
    return ips, ipRanges