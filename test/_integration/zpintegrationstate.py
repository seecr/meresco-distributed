# -*- coding: utf-8 -*-
## begin license ##
#
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  initiated by Stichting Bibliotheek.nl to provide a new search service
#  for all public libraries in the Netherlands.
# This package provides loadbalancer scripts
#
# Copyright (C) 2012-2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from os.path import isdir, isfile, join, abspath, dirname, basename
from os import chmod, makedirs
from subprocess import Popen
from time import time, sleep
from uuid import uuid4
from random import choice

from meresco.components import readConfig

from seecr.test.integrationtestcase import IntegrationState
from seecr.test.portnumbergenerator import PortNumberGenerator
from seecr.test.utils import getRequest, postRequest, postMultipartForm
from seecr.test.mockserver import MockServer

newId = lambda: str(uuid4())

mydir = dirname(abspath(__file__))
projectDir = dirname(dirname(dirname(mydir)))
documentationDir = join(projectDir, "doc")

class ZpIntegrationState(IntegrationState):
    def __init__(self, stateName, tests=None, fastMode=False):
        IntegrationState.__init__(self, "failover-" + stateName, tests=tests, fastMode=fastMode)

        self.testdataDir = join(dirname(mydir), 'data/integration')
        self.adminPort = PortNumberGenerator.next()
        self.adminServer = MockServer(self.adminPort)
        self.nginxConfigDir = join(self.integrationTempdir, 'nginx-conf.d')
        isdir(self.nginxConfigDir) or makedirs(self.nginxConfigDir)
        nginxScript = join(self.integrationTempdir, 'etc-init.d-nginx')
        self.nginxReloadCommand = "{0} reload".format(nginxScript)
        self.nginxScriptResult = join(self.integrationTempdir, 'etc-init.d-nginx-result')
        with open(nginxScript, 'w') as f:
            f.write('#!/bin/bash\necho "$(date +%%s) $@" > %s' % self.nginxScriptResult)
        chmod(nginxScript, 0770)

    def binDir(self, executable=None):
        binDir = join(projectDir, 'bin')
        if not isdir(binDir):
            binDir = '/usr/bin'
        return binDir if executable is None else join(binDir, executable)

    def setUp(self):
        self.adminServer.start()

    def tearDown(self):
        self.adminServer.halt = True
        IntegrationState.tearDown(self)

    def runNginxUpdateConfigNoDefaults(self, **kwargs):
        return self._runExecutable(join(self.binDir(), 'nginx-update-config'), **kwargs)

    def runNginxUpdateConfig(self, type, **kwargs):
        return self.runNginxUpdateConfigNoDefaults(adminHostname='localhost', adminPort=self.adminPort, type=type, nginxConfigDir=self.nginxConfigDir, nginxReload=self.nginxReloadCommand, **kwargs)
