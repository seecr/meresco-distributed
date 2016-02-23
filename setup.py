#!/usr/bin/env python
# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2015 Stichting Kennisnet http://www.kennisnet.nl
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
from os.path import join

data_files = []
for path, dirs, files in walk('usr-share'):
        data_files.append((path.replace('usr-share', '/usr/share/meresco-distributed', 1), [join(path, f) for f in files]))
for path, dirs, files in walk('etc'):
        data_files.append((path.replace('etc', '/etc', 1), [join(path, f) for f in files]))
scripts = []
for path, dirs, files in walk('bin'):
    for file in files:
        scripts.append(join(path, file))
packages = []
for path, dirs, files in walk('meresco'):
    if '__init__.py' in files and path != 'meresco':
        packages.append(path.replace('/', '.'))

setup(
    name='meresco-distributed',
    packages=[
        'meresco',                          #DO_NOT_DISTRIBUTE
    ] + packages,
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
