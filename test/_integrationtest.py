## begin license ##
#
# Drents Archief beoogt het Drents erfgoed centraal beschikbaar te stellen.
#
# Copyright (C) 2012-2014, 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2016 Drents Archief http://www.drentsarchief.nl
#
# This file is part of "Drents Archief"
#
# "Drents Archief" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Drents Archief" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Drents Archief"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from os import getuid
assert getuid() != 0, "Do not run tests as 'root'"

from seecrdeps import includeParentAndDeps       #DO_NOT_DISTRIBUTE
includeParentAndDeps(__file__, scanForDeps=True) #DO_NOT_DISTRIBUTE

from seecr.test.testrunner import TestRunner
from ._integration import IntegrationState

if __name__ == '__main__':
    runner = TestRunner()
    IntegrationState(
        "default",
        tests=[
            '_integration.nginxupdateconfigtest.NginxUpdateConfigTest',
        ],
        fastMode=runner.fastMode).addToTestRunner(runner)
    runner.run()


