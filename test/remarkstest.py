## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.distributed.remarks import Remarks
from weightless.core import consume

class RemarksTest(SeecrTestCase):

    def testStore(self):
        r = Remarks(self.tempdir)
        consume(r.handleRequest(Method="POST", path="/some/path/save", Body="key=key&contents=Contents"))
        self.assertEquals('Contents', r.getRemarks(key='key'))

    def testIsStored(self):
        r = Remarks(self.tempdir)
        consume(r.handleRequest(Method="POST", path="/some/path/save", Body="key=key&contents=The+contents"))
        self.assertEquals('The contents', Remarks(self.tempdir).getRemarks('key'))

    def testEmptyForNonExistingKey(self):
        self.assertEquals('', Remarks(self.tempdir).getRemarks(key='does_not_exist'))

    def testSaveEmptyKey(self):
        r = Remarks(self.tempdir)
        consume(r.handleRequest(Method="POST", path="/some/path/save", Body="key=key&contents="))
        self.assertEquals('', r.getRemarks(key='key'))
