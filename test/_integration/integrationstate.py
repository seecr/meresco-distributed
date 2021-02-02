# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2014, 2016, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from os.path import isdir, join, abspath, dirname
from os import chmod, makedirs
from uuid import uuid4
from time import sleep
from seecr.test.integrationtestcase import IntegrationState as _IntegrationState
from meresco.testsupport.mockadminserver import MockAdminServer
from seecr.test.portnumbergenerator import PortNumberGenerator

newId = lambda: str(uuid4())

mydir = dirname(abspath(__file__))
projectDir = dirname(dirname(mydir))

class IntegrationState(_IntegrationState):
    def __init__(self, stateName, tests=None, fastMode=False):
        _IntegrationState.__init__(self, "failover-" + stateName, tests=tests, fastMode=fastMode)

        self.testdataDir = join(dirname(mydir), 'data/integration')
        self.adminPort = PortNumberGenerator.nextPort()
        self.nginxConfigDir = join(self.integrationTempdir, 'nginx-conf.d')
        isdir(self.nginxConfigDir) or makedirs(self.nginxConfigDir)
        nginxScript = join(self.integrationTempdir, 'etc-init.d-nginx')
        self.nginxReloadCommand = "{0} reload".format(nginxScript)
        self.nginxScriptResult = join(self.integrationTempdir, 'etc-init.d-nginx-result')
        with open(nginxScript, 'w') as f:
            f.write('#!/bin/bash\necho "$(date +%%s) $@" > %s' % self.nginxScriptResult)
        self.config = {
            "api.frontend": {
                "fqdn": "example.org"
            }
        }
        chmod(nginxScript, 0o770)

    def binDir(self):
        return join(projectDir, 'bin')

    def setUp(self):
        self.startMockAdminServer()
        self.waitForServicesStarted()
        sleep(0.2)

    def startMockAdminServer(self):
        self.mockAdminServer = MockAdminServer(self.adminPort)
        self.mockAdminServer.configUpdate = self.config
        self.mockAdminServer.start()

    def runNginxUpdateConfigNoDefaults(self, **kwargs):
        return self._runExecutable(executable=self.binPath('nginx-update-config'), **kwargs)

    def runNginxUpdateConfig(self, type, **kwargs):
        return self.runNginxUpdateConfigNoDefaults(adminHostname='localhost', adminPort=self.adminPort, type=type, nginxConfigDir=self.nginxConfigDir, nginxReload=self.nginxReloadCommand, sharedSecret="test", **kwargs)
