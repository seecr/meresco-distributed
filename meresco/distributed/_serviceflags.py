## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2014-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

SERVICE_FLAGS = {}
class _Flag(object):
    def __init__(self, name, default):
        self.name = name
        self.default = default
        SERVICE_FLAGS[name] = self

    def isSet(self, d):
        return d.get(self.name, self.default)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.name))


READABLE = _Flag('readable', default=False)
WRITABLE = _Flag('writable', default=False)
_Flag.__init__ = None

class CombinedFlag(object):
    def __init__(self, flags):
        self._flags = flags
        self.name = '/'.join(f.name for f in flags)
        self.__str__ = lambda: self.name

    def isSet(self, d):
        return all(f.isSet(d) for f in self._flags)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.name))

READWRITE = CombinedFlag([READABLE, WRITABLE])

