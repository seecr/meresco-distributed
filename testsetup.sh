#!/bin/bash
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

set -e
mydir=$(cd $(dirname $0);pwd)

source /usr/share/seecr-tools/functions.d/test

rm -rf tmp build

definePythonVars

$PYTHON setup.py install --root tmp
cp -r test tmp/test

removeDoNotDistribute tmp
find tmp -type f -exec sed -e \
    "s,usrSharePath = .*,usrSharePath = '$mydir/tmp/usr/share/zp-loadbalancer',;
    s,binDir = '/usr/bin',binDir = '$mydir/tmp/usr/local/bin',;
    " -i {} \;

export ZP_SKIP_TESTRESULT_LOGGING="TRUE"
export SEECRTEST_USR_BIN="${mydir}/tmp/usr/local/bin"
if [ -z "$@" ]; then
    runtests "alltests.sh integrationtest.sh"
else
    runtests "$@"
fi

rm -rf tmp build
