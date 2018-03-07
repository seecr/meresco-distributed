## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2016, 2018 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2016 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2016 SURFmarket https://surf.nl
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

from .__version__ import VERSION
from ._proxy import Proxy
from ._serviceconfig import ServiceConfig
from ._sslconfig import SslConfig
from ._staticpathconfig import StaticPathConfig, StaticLocations, StaticServiceConfig, StaticServerName, StaticListenLine
from ._unusedconfig import UnusedConfig
from ._httptohttpsredirect import HttpToHttpsRedirect
from ._matchesversion import MatchesVersion
from ._conditionmet import ConditionMet
from .failover import Failover
NginxConfig = Proxy
