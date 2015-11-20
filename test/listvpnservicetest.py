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

from seecr.test import SeecrTestCase, CallTrace
from meresco.distributed import Service, ListVpnService
from weightless.core import consume

class ListVpnServiceTest(SeecrTestCase):
    def testChangeIp(self):
        def services(*args, **kwargs):
            return {
                "id0": Service(identifier="id0", ipAddress="1.2.3.4", data={}),
                "id1": Service(identifier="id1", ipAddress="1.2.3.5", data={}),
            }
        observer = CallTrace(methods=dict(listServices=services))
        lvs = ListVpnService()
        lvs.addObserver(observer)
        self.assertEquals('1.2.3.4', lvs.listServices()['id0']['ipAddress'])
        consume(lvs.updateConfig(config={
                "vpn":{
                    "convert-ips": {
                        "real": "vpn",
                        "1.2.3.4": "10.20.30.40"
                    }
                }
            }))
        self.assertEquals('1.2.3.4', lvs.listServices()['id0']['ipAddress'])
        self.assertEquals('10.20.30.40', lvs.listServices(convertIpsToVpn=True)['id0']['ipAddress'])
        self.assertEquals('1.2.3.4', lvs.listServices(convertIpsToVpn=True)['id0']['data']['originalIpAddress'])
        self.assertEquals('1.2.3.5', lvs.listServices(convertIpsToVpn=True)['id1']['ipAddress'])



