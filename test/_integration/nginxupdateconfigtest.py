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

from seecr.test.integrationtestcase import IntegrationTestCase
from uuid import uuid4

from meresco.components.json import JsonDict

newId = lambda: str(uuid4())

class NginxUpdateConfigTest(IntegrationTestCase):
    def setUp(self):
        IntegrationTestCase.setUp(self)
        del self.adminServer.requests[:]

    def testRunWithoutParams(self):
        result = self.runNginxUpdateConfigNoDefaults(expectedReturnCode=1)
        self.assertTrue('-h, --help' in result, result)

    def testRunNormal(self):
        self.adminServer.response = JsonDict({
            'services': {
                newId(): {'type': 'api', 'active': True, 'ipAddress': '10.0.0.10', 'infoport': 1234, 'data':{'VERSION': '0.42'}},
            },
            'config': {
                'api.frontend': {
                    'ipAddress': '10.1.2.3',
                    'fqdn': 'api.frontend.example.org',
                    'reconfiguration.interval': 1,
                }
            },
        }).pretty_print()
        self.runNginxUpdateConfig(processName='testRunNormal', type='api', minVersion='0.40', untilVersion='1.0')
        self.assertEquals(1, len(self.adminServer.requests))
        header, body = self.adminServer.requests[0].split('\r\n\r\n')
        self.assertTrue('GET /api/service/v2/list' in header, header)

