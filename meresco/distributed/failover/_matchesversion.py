## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2018 Seecr (Seek You Too B.V.) http://seecr.nl
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

from ._conditionmet import ConditionMet

from meresco.components.version import Version

def betweenVersionCondition(minVersion, untilVersion):
    minVersion, untilVersion = Version.create(minVersion), Version.create(untilVersion)
    def fn(software_version=None, **kwargs):
        return not software_version is None and \
            minVersion <= Version.create(software_version) < untilVersion
    return fn

class MatchesVersion(ConditionMet):
    def __init__(self, minVersion, untilVersion, **kwargs):
        ConditionMet.__init__(self, condition=betweenVersionCondition(minVersion, untilVersion), **kwargs)

