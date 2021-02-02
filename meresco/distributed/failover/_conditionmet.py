## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2018, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2021 SURF https://www.surf.nl
# Copyright (C) 2021 Stichting Kennisnet https://www.kennisnet.nl
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


from weightless.core import NoneOfTheObserversRespond, DeclineMessage
from meresco.core import Observable

class ConditionMet(Observable):
    def __init__(self, condition, **kwargs):
        Observable.__init__(self, **kwargs)
        self._conditionMet = False
        self._condition_test = condition

    def updateConfig(self, **kwargs):
        yield self.all.updateConfig(**kwargs)
        self._conditionMet = self._condition_test(**kwargs)

    def all_unknown(self, message, *args, **kwargs):
        if self._conditionMet:
            yield self.all.unknown(message, *args, **kwargs)

    def any_unknown(self, message, *args, **kwargs):
        if self._conditionMet:
            try:
                response = yield self.any.unknown(message, *args, **kwargs)
                return response
            except NoneOfTheObserversRespond:
                pass
        raise DeclineMessage

    def do_unknown(self, message, *args, **kwargs):
        if self._conditionMet:
            self.do.unknown(message, *args, **kwargs)

    def call_unknown(self, message, *args, **kwargs):
        if self._conditionMet:
            try:
                return self.call.unknown(message, *args, **kwargs)
            except NoneOfTheObserversRespond:
                pass
        raise DeclineMessage
