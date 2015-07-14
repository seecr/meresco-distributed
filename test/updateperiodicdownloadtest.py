## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2013-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from seecr.test import SeecrTestCase, CallTrace

from weightless.core import compose
from meresco.components import Schedule

from meresco.distributed.constants import OAI_DOWNLOAD_PERIOD_CONFIG_KEY, READABLE
from meresco.distributed import UpdatePeriodicDownload


class UpdatePeriodicDownloadTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        pdStateMock = Bucket(
            host=None,
            port=None,
            schedule=Schedule(period=1),
            paused=False)

        def setDownloadAddress(host, port):
            pdStateMock.host = host
            pdStateMock.port = port

        def setSchedule(schedule):
            pdStateMock.schedule = schedule

        def pause():
            pdStateMock.paused = True

        def resume():
            pdStateMock.paused = False


        self.serviceManagementMock = CallTrace(
            'serviceManagement',
            ignoredAttributes=['setDownloadAddress', 'setSchedule', 'pause', 'resume'],
            returnValues={'selectHostPortForService': ('hostname', 1234)},
        )
        self.periodicDownloadMock = CallTrace(
            'periodicDownload',
            ignoredAttributes=['selectHostPortForService', 'call_unknown'],
            returnValues={'getState': pdStateMock},
            methods={
                'setDownloadAddress': setDownloadAddress,
                'setSchedule': setSchedule,
                'pause': pause,
                'resume': resume,
            },
        )

        self.updatePeriodicDownload = UpdatePeriodicDownload(
                serviceIdentifier='identifier',
                periodicDownloadName='sourceService',
                sourceServiceType='sourceServiceType',
                name='sourceService')
        self.updatePeriodicDownload.addObserver(self.periodicDownloadMock)
        self.updatePeriodicDownload.addObserver(self.serviceManagementMock)

    def testUpdateConfig(self):
        list(compose(self.updatePeriodicDownload.updateConfig(
            config={
                OAI_DOWNLOAD_PERIOD_CONFIG_KEY: 2,
                'identifier.periodicDownload.sourceService.paused': True
            },
            services={
                'sourceServiceIdentifier': {
                    'type': 'sourceServiceType',
                    'host': 'hostname',
                    'port': 1234,
                    'readable': True,
                },
                'identifier': {
                    'writable': True,
                }
            }
        )))
        self.assertEquals(['getState', 'setSchedule', 'setDownloadAddress', 'pause'], self.periodicDownloadMock.calledMethodNames())
        self.assertEquals(2, self.periodicDownloadMock.calledMethods[1].kwargs['schedule'].period)
        self.assertEquals(['selectHostPortForService'], self.serviceManagementMock.calledMethodNames())
        self.assertEquals(True, self.serviceManagementMock.calledMethods[0].kwargs['remember'])

        self.periodicDownloadMock.calledMethods.reset()
        self.serviceManagementMock.calledMethods.reset()

        list(compose(self.updatePeriodicDownload.updateConfig(
            config={
                OAI_DOWNLOAD_PERIOD_CONFIG_KEY: 2,
                'identifier.periodicDownload.sourceService.paused': False
            },
            services={
                'sourceServiceIdentifier': {
                    'type': 'sourceServiceType',
                    'host': 'hostname',
                    'port': 1234,
                    'readable': True,
                },
                'identifier': {
                    'writable': True,
                }
            }
        )))
        self.assertEquals(['getState', 'resume'], self.periodicDownloadMock.calledMethodNames())
        self.assertEquals(['selectHostPortForService'], self.serviceManagementMock.calledMethodNames())
        self.assertEquals(True, self.serviceManagementMock.calledMethods[0].kwargs['remember'])

        self.periodicDownloadMock.calledMethods.reset()
        self.serviceManagementMock.calledMethods.reset()

        # writable = False
        list(compose(self.updatePeriodicDownload.updateConfig(
            config={
                OAI_DOWNLOAD_PERIOD_CONFIG_KEY: 2,
            },
            services={
                'sourceServiceIdentifier': {
                    'type': 'sourceServiceType',
                    'host': 'hostname',
                    'port': 1234,
                    'readable': True,
                },
                'identifier': {
                    'type': 'sourceServiceType',
                    'host': 'hostname',
                    'port': 1235,
                    'writable': False
                }
            }
        )))
        self.assertEquals(['getState', 'pause'], self.periodicDownloadMock.calledMethodNames())

        self.periodicDownloadMock.calledMethods.reset()
        self.serviceManagementMock.calledMethods.reset()

        list(compose(self.updatePeriodicDownload.updateConfig(
            config={},
            services={
                'sourceServiceIdentifier': {
                    'type': 'sourceServiceType',
                    'host': 'hostname',
                    'port': 1234,
                    'readable': True,
                },
                'identifier': {
                    'type': 'sourceServiceType',
                    'host': 'hostname',
                    'port': 1235,
                    'writable': True,
                }
            }
        )))
        self.assertEquals(['getState', 'setSchedule', 'resume'], self.periodicDownloadMock.calledMethodNames())
        self.assertEquals(['selectHostPortForService'], self.serviceManagementMock.calledMethodNames())
        self.assertEquals(True, self.serviceManagementMock.calledMethods[0].kwargs['remember'])

    def testGetPollIntervalFromConfigSelectorOnUpdateConfig(self):
        observers = self.updatePeriodicDownload.observers()
        self.updatePeriodicDownload = UpdatePeriodicDownload(
                serviceIdentifier='identifier',
                periodicDownloadName='sourceService',
                pollIntervalConfigSelector=(lambda config: config['some']['deeply'][0]['nested'][0]),
                sourceServiceType='sourceServiceType',
                name='sourceService'
            )
        [self.updatePeriodicDownload.addObserver(o) for o in observers]
        self.serviceManagementMock.returnValues.pop('selectHostPortForService')
        self.serviceManagementMock.exceptions['selectHostPortForService'] = ValueError('Ka-Boom')

        list(compose(self.updatePeriodicDownload.updateConfig(
            config={
                'some': {
                    'deeply': [
                        {'nested': [7]},
                    ],
                },
            },
            services={}
        )))

        self.assertEquals(['getState', 'setSchedule', 'pause'], self.periodicDownloadMock.calledMethodNames())
        self.assertEquals(7, self.periodicDownloadMock.calledMethods[1].kwargs['schedule'].period)
        self.assertEquals(True, self.serviceManagementMock.calledMethods[0].kwargs['remember'])

        self.periodicDownloadMock.calledMethods.reset()
        self.serviceManagementMock.calledMethods.reset()

    def testShouldPauseWhenSourceIsUnreadable(self):
        self.serviceManagementMock.returnValues['selectHostPortForService'] = (None, None)
        list(compose(self.updatePeriodicDownload.updateConfig(
            config={
                OAI_DOWNLOAD_PERIOD_CONFIG_KEY: 2,
            },
            services={
                'sourceServiceIdentifier': {
                    'type': 'sourceServiceType',
                    'host': 'hostname',
                    'port': 1234,
                    'readable': True,
                },
                'identifier': {
                    'writable': True,
                }
            }
        )))
        self.assertEquals(['getState', 'setSchedule', 'pause'], self.periodicDownloadMock.calledMethodNames())

        self.periodicDownloadMock.calledMethods.reset()
        self.serviceManagementMock.returnValues['selectHostPortForService'] = ('hostname', 1234)
        list(compose(self.updatePeriodicDownload.updateConfig(
            config={
                OAI_DOWNLOAD_PERIOD_CONFIG_KEY: 2,
            },
            services={
                'sourceServiceIdentifier': {
                    'type': 'sourceServiceType',
                    'host': 'hostname',
                    'port': 1234,
                    'readable': True     # not actually used in test, but shows intent
                },
                'identifier': {
                    'writable': True,
                }
            }
        )))
        self.assertEquals(['getState', 'setDownloadAddress', 'resume'], self.periodicDownloadMock.calledMethodNames())

    def testCreateUpdatePeriodicDownloadForSpecificService(self):
        self.updatePeriodicDownload = UpdatePeriodicDownload(
                serviceIdentifier='identifier',
                periodicDownloadName='sourceService',
                sourceServiceType='sourceServiceType',
                sourceServiceIdentifier='sourceServiceIdentifier',
                name='sourceService')
        self.updatePeriodicDownload.addObserver(self.periodicDownloadMock)
        self.updatePeriodicDownload.addObserver(self.serviceManagementMock)

        list(compose(self.updatePeriodicDownload.updateConfig(
            config={},
            services={
                'sourceServiceIdentifier': {
                    'type': 'sourceServiceType',
                    'host': 'hostname',
                    'port': 1234,
                    'readable': True,
                },
                'identifier': {
                    'writable': True,
                }
            }
        )))

        self.assertEqual(['selectHostPortForService'], self.serviceManagementMock.calledMethodNames())
        self.assertEqual({
                'flag': READABLE,
                'identifier': 'sourceServiceIdentifier',
                'remember': True,
                'type': 'sourceServiceType'
            }, self.serviceManagementMock.calledMethods[0].kwargs)

class Bucket(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
