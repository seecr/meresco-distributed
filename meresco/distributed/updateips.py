## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from meresco.core import Observable

from .utils import ipsAndRanges as defaultIpsAndRanges

class UpdateIps(Observable):
    def __init__(self, configSelector, staticIpAddresses=None, includeLocalhost=True, name=None, ipsAndRanges=None):
        Observable.__init__(self, name=name)
        self._configSelector = configSelector
        self._staticIpAddresses = set(staticIpAddresses) if staticIpAddresses is not None else set()
        self._includeLocalhost = includeLocalhost
        self._ipsAndRanges = defaultIpsAndRanges if ipsAndRanges is None else ipsAndRanges

    def updateConfig(self, config, **kwargs):
        ips, ipRanges = self._ipsAndRanges(self._getFromConfig(config), includeLocalhost=self._includeLocalhost)
        if self._staticIpAddresses:
            ips.update(self._staticIpAddresses)
        self.do.updateIps(ipAddresses=ips, ipRanges=ipRanges)
        return
        yield

    def _getFromConfig(self, config):
        return self._configSelector(config)

