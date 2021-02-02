## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2014-2015, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from seecr.test import SeecrTestCase
from meresco.distributed.servicelog import ServiceLog, tai64ToTime
from os.path import join
from os import makedirs

class ServiceLogTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.log = ServiceLog(identifier='identifier', serviceDir=self.tempdir)

    def testGetLogFilesNoneIfNotInitialized(self):
        self.assertEqual([], self.log.getLogFiles())

    def testGetLogFiles(self):
        logdir = join(self.tempdir, 'zp-serviceType-identifier', 'log', 'main')
        makedirs(logdir)
        for f in ['@4000000052abf8200d2edecc.s', '@4000000052ad8cb729667ce4.u', 'current', 'lock', 'state']:
            with open(join(logdir, f), 'w'):
                pass
        self.assertEqual([
            ('zp-serviceType-identifier', 'current'),
            ('zp-serviceType-identifier', '@4000000052ad8cb729667ce4.u'),
            ('zp-serviceType-identifier', '@4000000052abf8200d2edecc.s'),
            ], [(d, f) for d, f, timestamp in self.log.getLogFiles()])

    def testGetLogFilesForTwoDirs(self):
        logdir = join(self.tempdir, 'zp-gateway-identifier', 'log', 'main')
        logdir2 = join(self.tempdir, 'zp-gateway-identifier-rdf-validator', 'log', 'main')
        makedirs(logdir)
        makedirs(logdir2)
        for f in ['@4000000052abf8200d2edecc.s', '@4000000052ad8cb729667ce4.u', 'current', 'lock', 'state']:
            for l in [logdir, logdir2]:
                with open(join(l, f), 'w'):
                    pass
        self.assertEqual([
            ('zp-gateway-identifier', 'current'),
            ('zp-gateway-identifier', '@4000000052ad8cb729667ce4.u'),
            ('zp-gateway-identifier', '@4000000052abf8200d2edecc.s'),
            ('zp-gateway-identifier-rdf-validator', 'current'),
            ('zp-gateway-identifier-rdf-validator', '@4000000052ad8cb729667ce4.u'),
            ('zp-gateway-identifier-rdf-validator', '@4000000052abf8200d2edecc.s'),
            ], [(d, f) for d, f, timestamp in self.log.getLogFiles()])

    def testGetLogLines(self):
        logdir = join(self.tempdir, 'zp-serviceType-identifier', 'log', 'main')
        makedirs(logdir)
        with open(join(logdir, '@4000000052abf8200d2edecc.s'), 'w') as f:
            f.write('@4000000052abf8100d2edecc line0\n')
            f.write('@4000000052abf8190d2edecc line1\n')
        r = self.log.getLogLines(dirname='zp-serviceType-identifier', filename='@4000000052abf8200d2edecc.s')
        self.assertEqual([
                ('2013-12-14 07:17:42.221', 'line0\n'),
                ('2013-12-14 07:17:51.221', 'line1\n'),
            ], list(r))
        r = self.log.getLogLines(dirname='zp-serviceType-identifier', filename='@4000000052abf8200d2edecc.s', filterValue='line0')
        self.assertEqual([
                ('2013-12-14 07:17:42.221', 'line0\n'),
            ], list(r))
        r = self.log.getLogLines(dirname='zp-serviceType-identifier', filename='@4000000052abf8200d2edecc.s', filterStamp='17:51')
        self.assertEqual([
                ('2013-12-14 07:17:51.221', 'line1\n'),
            ], list(r))

    def testFormatTimestamp(self):
        self.assertEqual('2013-12-14 07:17:51.221', tai64ToTime('@4000000052abf8190d2edecc'))


