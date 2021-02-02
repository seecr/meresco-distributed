## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2016, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2016 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2021 SURF https://www.surf.nl
# Copyright (C) 2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from seecr.test.integrationtestcase import IntegrationTestCase
from uuid import uuid4
from meresco.distributed.constants import ADMIN_DOWNLOAD_PERIOD_CONFIG_KEY

newId = lambda: str(uuid4())

class NginxUpdateConfigTest(IntegrationTestCase):
    def setUp(self):
        IntegrationTestCase.setUp(self)
        del self.mockAdminServer.requests[:]

    def testRunWithoutParams(self):
        result = self.runNginxUpdateConfigNoDefaults(expectedReturnCode=2)
        self.assertTrue('usage: nginx-update-config [-h]' in result, result)

    def testRunNormal(self):
        self.mockAdminServer.configUpdate = {
            'services': {
                newId(): {'type': 'api', 'active': True, 'ipAddress': '10.0.0.10', 'infoport': 1234, 'data':{'VERSION': '0.42'}},
            },
            'config': {
                'api.frontend': {
                    'ipAddress': '10.1.2.3',
                    'fqdn': 'api.frontend.example.org',
                },
                ADMIN_DOWNLOAD_PERIOD_CONFIG_KEY: 1,
            },
        }
        self.runNginxUpdateConfig(processName='testRunNormal', type='api', minVersion='0.40', untilVersion='1.0')
        self.assertEqual(1, len(self.mockAdminServer.requests))
        header, body = self.mockAdminServer.requests[0].split(b'\r\n\r\n')
        self.assertTrue(b'POST /api/service/v2/update' in header, header)

