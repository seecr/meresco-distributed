## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.core import Transparent

class ListVpnService(Transparent):
    def __init__(self, **kwargs):
        Transparent.__init__(self, **kwargs)
        self._convertDict = {}

    def updateConfig(self, config, **kwargs):
        self._convertDict = config.get('vpn', {}).get('convert-ips',{})
        return
        yield

    def listServices(self, *args, **kwargs):
        convertIps = kwargs.pop('convertIpsToVpn', False)
        services = self.call.listServices(*args, **kwargs)
        if convertIps:
            for service in services.values():
                ipAddress = service['ipAddress']
                vpnAddress = self._convertDict.get(ipAddress, ipAddress)
                if vpnAddress != ipAddress:
                    service['ipAddress'] = vpnAddress
                    service['data']['originalIpAddress'] = ipAddress
        return services
