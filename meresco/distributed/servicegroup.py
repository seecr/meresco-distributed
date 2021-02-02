## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2016, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
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

from meresco.core import Transparent

class ServiceGroup(Transparent):
    def __init__(self, groupings=None, additionalGroupings=None, name=None):
        Transparent.__init__(self, name=name)
        self._groupingMethods = dict((g.key, g) for g in (_DEFAULT_GROUPINGS if groupings is None else groupings))
        if additionalGroupings:
            for g in additionalGroupings:
                self._groupingMethods[g.key] = g
        self._defaultGrouping = self._groupingMethods['default']

    def groupAndServices(self, groupingKey, **kwargs):
        services = self.call.listServices(**kwargs).items()
        serviceGroups = dict()
        grouping = self._groupingMethods.get(groupingKey, self._defaultGrouping)
        for identifier, service in services:
            serviceGroups.setdefault(grouping(service), []).append(service)
        return [(groupName, sorted(s, key=lambda s:(s['type'], s['number']))) for (position, groupName), s in sorted(serviceGroups.items())]

    def listGroupings(self):
        return sorted(((g.key, g.name) for g in self._groupingMethods.values()), key=lambda key_name:(key_name[1],key_name[0]))


class GroupingIp(object):
    key='ip'
    name='IP-Address'
    def __call__(self, service):
        return (1, 'IP: {0}'.format(service['ipAddress']))

class GroupingDefault(object):
    key='default'
    name='Default'
    def __call__(self, service):
        return (0, 'Default')

class GroupingError(object):
    key='error'
    name='Error'
    def __call__(self, service):
        if 'errors' in service.get('data', {}):
            return (0, 'Error')
        if 'warnings' in service.get('data', {}):
            return (1, 'Warning')
        return (99999, 'Ok')

class GroupingVersion(object):
    key='version'
    name='Version'
    def __call__(self, service):
        return (0, 'Version {0}'.format(service.get('data', {'VERSION': '?'}).get('VERSION', '?')))

class GroupingOnOff(object):
    key='rw'
    name='On/Off'
    def __call__(self, service):
        if service.get('writable') and service.get('readable'):
            return (0, 'Readable and writable')
        if service.get('readable'):
            return (1, 'Readable')
        if service.get('writable'):
            return (2, 'Writable')
        return (3, 'Off')

_DEFAULT_GROUPINGS = [GroupingDefault(), GroupingIp(), GroupingError(), GroupingVersion(), GroupingOnOff()]
