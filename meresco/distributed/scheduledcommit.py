## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2018 SURF http://www.surf.nl
# Copyright (C) 2018 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2018 Stichting Kennisnet https://www.kennisnet.nl
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

from weightless.core import be
from meresco.core import Transparent
from meresco.core.alltodo import AllToDo
from meresco.components import PeriodicCall, Schedule
from .updateperiodiccall import UpdatePeriodicCall

class InsideOutObservable(object):
    def __init__(self, **kwargs):
        self.internalObserverTreeRoot = Transparent(**kwargs)
        self.outside = Transparent(name='outside')
        self.addObserver = self.outside.addObserver
        self.addStrand = self.outside.addStrand
        self.call = self.outside.call
        self.do = self.outside.do
        self.all = self.outside.all
        self.any = self.outside.any
        self.once = self.internalObserverTreeRoot.once

    def observer_init(self):
        yield self.once.observer_init()

    def handleShutdown(self):
        yield self.once.handleShutdown()

class ScheduledCommit(InsideOutObservable):
    def __init__(self, reactor, name=None, **kwargs):
        InsideOutObservable.__init__(self, name=name or 'scheduledCommit', **kwargs)
        self._scheduledCommit = be(
            (PeriodicCall(reactor, message='commit', autoStart=False, name='Scheduled commit', errorSchedule=Schedule(period=1)),
                (AllToDo(),
                    (self.outside,)
                )
            )
        )
        self.internalObserverTreeRoot.addObserver(self._scheduledCommit)

    def configObserver(self):
        return be(
            (UpdatePeriodicCall(scheduleConfigKey='global.scheduledCommitSchedule', default=dict(period=3600)),
                (self._scheduledCommit,)
            )
        )

    def getState(self):
        return self._scheduledCommit.getState()

