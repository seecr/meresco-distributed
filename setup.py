#!/usr/bin/env python3
# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015-2016, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2015, 2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2021 SURF https://www.surf.nl
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

from distutils.core import setup
from os import walk
from os.path import join, relpath

data_files = []
for path, dirs, files in walk('usr-share'):
        data_files.append((path.replace('usr-share', '/usr/share/meresco-distributed', 1), [join(path, f) for f in files]))
scripts = []
for path, dirs, files in walk('bin'):
    for file in files:
        scripts.append(join(path, file))
packages = []
for path, dirs, files in walk('meresco'):
    if '__init__.py' in files and path != 'meresco':
        packages.append(path.replace('/', '.'))
package_data = {}
for path, dirs, files in walk('meresco/distributed'):
    for ext in ['sf']:
        if any(f.endswith('.'+ext) for f in files):
            filepath = join(path, '*.'+ext)
            filepath = relpath(filepath, 'meresco/distributed')
            package_data.setdefault('meresco.distributed', []).append(filepath)

setup(
    name='meresco-distributed',
    packages=[
        'meresco',                          #DO_NOT_DISTRIBUTE
    ] + packages,
    package_data=package_data,
    data_files=data_files,
    scripts=scripts,
    version='%VERSION%',
    url='http://seecr.nl',
    author='Seecr (Seek You Too B.V.)',
    author_email='info@seecr.nl',
    description='Meresco Distributed has components for group management based on Meresco Components.',
    long_description='Meresco Distributed has components for group management based on Meresco Components.',
    license='GPL',
    platforms='all',
)
