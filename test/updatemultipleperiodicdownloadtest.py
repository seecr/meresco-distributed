## begin license ##
#
# "Edurep" is a service for searching in educational repositories.
# "Edurep" is developed for Stichting Kennisnet (http://www.kennisnet.nl) by
# Seek You Too (http://www.cq2.nl). The project is based on the opensource
# project Meresco (http://www.meresco.com).
#
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2015 Stichting Kennisnet http://www.kennisnet.nl
#
# This file is part of "Edurep"
#
# "Edurep" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Edurep" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Edurep"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from seecr.test import SeecrTestCase, CallTrace
from meresco.distributed.updatemultipleperiodicdownload import UpdateMultiplePeriodicDownload
from meresco.distributed import SelectService
from weightless.core import consume


class UpdateMultiplePeriodicDownloadTest(SeecrTestCase):

    def testOne(self):
        reactor = CallTrace()
        serviceManagement = CallTrace()
        downloadObserver = CallTrace()
        serviceSelector = SelectService(currentVersion='1.0')
        serviceManagement.returnValues['getServiceSelector'] = serviceSelector
        mup = UpdateMultiplePeriodicDownload(reactor=reactor, serviceManagement=serviceManagement, createDownloadObserver=downloadObserver.create, name='type', downloadPath='/oai', serviceType='repository', metadataPrefix='records', statePath=self.tempdir)

        updateConfigKwargs = dict(services=dict([createService('id1', 1234)]))
        consume(serviceSelector.updateConfig(**updateConfigKwargs))
        consume(mup.updateConfig(**updateConfigKwargs))
        self.assertEqual(1, len(mup.getState()))
        self.assertEqual(['create'], downloadObserver.calledMethodNames())
        kwargs = downloadObserver.calledMethods[0].kwargs
        self.assertEqual("id1", kwargs['identifier'])
        self.assertEqual('type', kwargs['name'])
        self.assertTrue("periodicDownload" in kwargs, kwargs)
        self.assertTrue("oaiDownload" in kwargs, kwargs)

        updateConfigKwargs = dict(services=dict([
                createService('id1', 1234),
                createService('id2', 1235)
            ]))
        consume(serviceSelector.updateConfig(**updateConfigKwargs))
        consume(mup.updateConfig(**updateConfigKwargs))
        self.assertEqual(2, len(mup.getState()))

        updateConfigKwargs = dict(services=dict([
                createService('id1', 1234),
                createService('id2', 1235),
                createService('id3', 1236)
            ]))
        consume(serviceSelector.updateConfig(**updateConfigKwargs))
        consume(mup.updateConfig(**updateConfigKwargs))
        self.assertEqual(3, len(mup.getState()))

createService = lambda identifier, port: (
    identifier, {
        'identifier': identifier,
        'type': 'repository',
        'host': 'hostname',
        'port': port,
        'readable': True,
        'data': {'VERSION': '1.0'}
    })