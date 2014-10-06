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

from distutils.core import setup

version = '$Version: 0.1.x$'[9:-1].strip()

from os import walk
from os.path import join
data_files = []
for path, dirs, files in walk('usr-share'):
        data_files.append((path.replace('usr-share', '/usr/share/zp-loadbalancer', 1), [join(path, f) for f in files]))
for path, dirs, files in walk('etc'):
        data_files.append((path.replace('etc', '/etc', 1), [join(path, f) for f in files]))
for path, dirs, files in walk('sbin'):
        data_files.append((path.replace('sbin', '/sbin', 1), [join(path, f) for f in files]))
scripts = []
for path, dirs, files in walk('bin'):
    for file in files:
        scripts.append(join(path, file))
packages = []
for path, dirs, files in walk('zploadbalancer'):
    if '__init__.py' in files:
        packagename = path.replace('/', '.')
        packages.append(packagename)

setup(
    name='zp-loadbalancer',
    packages=packages,
    data_files=data_files,
    scripts=scripts,
    version=version,
    url='http://zp.seecr.nl',
    author='Seecr',
    author_email='development@seecr.nl',
    maintainer='Seecr',
    maintainer_email='development@seecr.nl',
    description='Loadbalancer service for ZP',
    long_description='Loadbalancer and failover service for ZP',
    license='All rights reserved.',
    platforms='all',
)
