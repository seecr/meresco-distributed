# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2015 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2016 SURFmarket https://surf.nl
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

from os import getuid
assert getuid() != 0, "Do not run tests as 'root'"

from seecrdeps import includeParentAndDeps       #DO_NOT_DISTRIBUTE
includeParentAndDeps(__file__)                   #DO_NOT_DISTRIBUTE
from os import system                            #DO_NOT_DISTRIBUTE
system('find .. -name "*.pyc" | xargs rm -f')    #DO_NOT_DISTRIBUTE

import unittest
from warnings import simplefilter
simplefilter('default')

from compositestatetest import CompositeStateTest
from configdownloadprocessortest import ConfigDownloadProcessorTest
from confighandlertest import ConfigHandlerTest
from configurationtest import ConfigurationTest
from crashdetecttest import CrashDetectTest
from flagchecktest import FlagCheckTest
from listvpnservicetest import ListVpnServiceTest
from remarkstest import RemarksTest
from selectservicetest import SelectServiceTest
from servicegrouptest import ServiceGroupTest
from servicehandlertest import ServiceHandlerTest
from servicelogtest import ServiceLogTest
from servicemanagementtest import ServiceManagementTest
from serviceregistrytest import ServiceRegistryTest
from servicestatetest import ServiceStateTest
from updateipstest import UpdateIpsTest
from updatemultipleperiodicdownloadtest import UpdateMultiplePeriodicDownloadTest
from updateperiodiccalltest import UpdatePeriodicCallTest
from updateperiodicdownloadtest import UpdatePeriodicDownloadTest
from utilstest import UtilsTest

from dynamic.servicespagetest import ServicesPageTest

from failover.nginxconfigtest import NginxConfigTest

if __name__ == '__main__':
    unittest.main()
