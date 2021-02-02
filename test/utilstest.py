## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2015, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from meresco.distributed import serviceUpdateHash

class UtilsTest(SeecrTestCase):
    def testServiceUpdateHash(self):
        hash1 = serviceUpdateHash(secret='1234', identifier='x', type='y', ipAddress='1.2.3.4', port=99)
        hash2 = serviceUpdateHash(secret='3411', identifier='xx', type='yy', ipAddress='2.2.3.4', port=98)
        self.assertNotEqual(hash1, hash2)
        self.assertEqual(40, len(hash1))
        self.assertEqual(40, len(hash2))

    def testArgumentsNotAllowed(self):
        self.assertRaises(TypeError, serviceUpdateHash, '1234', 'x', 'y', '1.2.3.4', 99)

    def testHashBasedOnKwargs(self):
        hash = serviceUpdateHash(secret='1234', a='a', b='b', c=3)
        hash2 = serviceUpdateHash(secret='1234', b='b', c=3, a='a')
        self.assertEqual(hash, hash2)
        self.assertEqual(40, len(hash))



