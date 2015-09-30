## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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
from meresco.distributed import CompositeState

class CompositeStateTest(SeecrTestCase):

    def testBothErrorState(self):
        state1 = State(errorState='WRONG')
        state2 = State(errorState='BAD')
        state = CompositeState(state1, state2)
        self.assertEquals('WRONG', state.errorState)

    def testOneErrorState(self):
        state1 = State(errorState='WRONG')
        state2 = State(errorState=None)
        state = CompositeState(state1, state2)
        self.assertEquals('WRONG', state.errorState)
        reversestate = CompositeState(state2, state1)
        self.assertEquals('WRONG', reversestate.errorState)

    def testOneOnlyWithErrorState(self):
        state1 = State(errorState='WRONG')
        state2 = State()
        state = CompositeState(state1, state2)
        self.assertEquals('WRONG', state.errorState)
        reversestate = CompositeState(state2, state1)
        self.assertEquals('WRONG', reversestate.errorState)

    def testErrorStatesNone(self):
        state1 = State(errorState=None)
        state2 = State(errorState=None)
        state = CompositeState(state1, state2)
        self.assertEquals(None, state.errorState)

    def testNoErrorState(self):
        state1 = State()
        state2 = State()
        state = CompositeState(state1, state2)
        self.assertRaises(AttributeError, lambda: state.errorState)

class State(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)