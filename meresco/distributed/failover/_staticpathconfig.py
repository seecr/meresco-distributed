## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2016 Seecr (Seek You Too B.V.) http://seecr.nl
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

class StaticPathConfig(object):
    def __init__(self, path, config):
        self._path = path
        self._config = config

    def locations(self):
        yield '   location {0} {{\n{1}\n    }}\n'.format(self._path, self._config)