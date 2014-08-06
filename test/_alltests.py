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

from os import getuid
assert getuid() != 0, "Do not run tests as 'root'"

from os import system                             #DO_NOT_DISTRIBUTE
from sys import path as sysPath                   #DO_NOT_DISTRIBUTE
system('find .. -name "*.pyc" | xargs rm -f')     #DO_NOT_DISTRIBUTE
                                                  #DO_NOT_DISTRIBUTE
from glob import glob                             #DO_NOT_DISTRIBUTE
for path in glob('../deps.d/*'):                  #DO_NOT_DISTRIBUTE
    sysPath.insert(0, path)                       #DO_NOT_DISTRIBUTE
sysPath.insert(0,'..')                            #DO_NOT_DISTRIBUTE

from unittest import main

from nginxconfigtest import NginxConfigTest

if __name__ == '__main__':
    main()

