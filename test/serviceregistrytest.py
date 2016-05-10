## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from os import stat, utime
from os.path import join
from uuid import uuid4
from time import time

from seecr.test import SeecrTestCase, CallTrace

from meresco.components.json import JsonDict
from meresco.distributed import ServiceRegistry
from meresco.distributed.serviceregistry import SERVICEREGISTRY_FILE
from meresco.distributed.constants import WRITABLE, READABLE, SERVICE_FLAGS


class ServiceRegistryTest(SeecrTestCase):
    def testShouldProcessUpdate(self):
        registry = ServiceRegistry(stateDir=self.tempdir, domainname="zp.example.org", reactor=CallTrace())
        observer = CallTrace('observer')
        registry.addObserver(observer)
        identifier = str(uuid4())
        registry.updateService(identifier=identifier, type='plein', ipAddress='127.0.0.1', infoport=1234, data={})
        services = registry.listServices()
        self.assertEquals(0, services[identifier]['number'])
        self.assertEquals('127.0.0.1', services[identifier]['ipAddress'])
        self.assertEquals(1234, services[identifier]['infoport'])
        self.assertEquals('plein', services[identifier]['type'])
        self.assertEquals(True, services[identifier].isActive())
        self.assertEquals('plein0.zp.example.org', services[identifier].fqdn())
        t0 = services[identifier]['lastseen']

        registry.updateService(identifier=identifier, type='plein', ipAddress='127.0.0.1', infoport=2345, data={})
        services = registry.listServices()
        self.assertEquals(0, services[identifier]['number'])
        self.assertEquals(2345, services[identifier]['infoport'])
        t1 = services[identifier]['lastseen']
        self.assertTrue(t0 < t1)

        identifier2 = str(uuid4())
        registry.updateService(identifier=identifier2, type='plein', ipAddress='127.0.0.2', infoport=1234, data={})
        self.assertEquals('plein1.zp.example.org', registry.getService(identifier2).fqdn())

        services = registry.listServices()
        self.assertEquals(2, len(services))

        registry = ServiceRegistry(stateDir=self.tempdir, reactor=CallTrace(), domainname="zp.example.org")
        observer = CallTrace('observer')
        registry.addObserver(observer)

        services = registry.listServices()
        self.assertEquals(0, services[identifier]['number'])
        self.assertEquals('127.0.0.1', services[identifier]['ipAddress'])
        self.assertEquals(2345, services[identifier]['infoport'])
        self.assertEquals('plein', services[identifier]['type'])
        self.assertEquals(2, len(services))

    def testShouldNotAllowTypesWithNumbers(self):
        registry = ServiceRegistry(stateDir=self.tempdir, reactor=CallTrace(), domainname='zp.example.org')
        observer = CallTrace('observer')
        registry.addObserver(observer)

        try:
            registry.updateService(identifier=str(uuid4()), type='aType1', ipAddress='127.0.0.1', infoport=1234, data={})
            self.fail('Should not happen')
        except ValueError, e:
            self.assertEquals('Service type "aType1" must not end with a number.', str(e))

        self.assertRaises(ValueError, lambda: registry.updateService(identifier=str(uuid4()), type='aType5', ipAddress='127.0.0.1', infoport=1234, data={}))

        registry.updateService(identifier=str(uuid4()), type='1234a', ipAddress='127.0.0.1', infoport=1234, data={})

        self.assertRaises(ValueError, lambda: registry.updateService(identifier='notAUUID', type='aType', ipAddress='127.0.0.1', infoport=1234, data={}))

    def testShouldCountServicesAsNotActiveAfterCertainTimeout(self):
        times = [12345678.0]
        registry = ServiceRegistry(stateDir=self.tempdir, reactor=CallTrace(), domainname='zp.example.org')
        observer = CallTrace('observer')
        registry.addObserver(observer)
        self.assertEquals(60, registry._timeout)
        self.assertEquals(24*60*60, registry._ultimateTimeout)
        def sleep(seconds):
            times[0] += seconds
        registry._now = lambda: times[0]

        identifier = str(uuid4())
        registry.updateService(identifier=identifier, type='plein', ipAddress='127.0.0.1', infoport=1234, data={})
        registry._services[identifier]._now = lambda: times[0]
        registry.setFlag(identifier, READABLE, True)
        registry.setFlag(identifier, WRITABLE, True)
        service = registry.listServices()[identifier]
        number = service['number']
        self.assertEquals(times[0], service['lastseen'])
        self.assertTrue(service.isActive())
        sleep(30)
        service = registry.listServices()[identifier]
        self.assertTrue(times[0] > service['lastseen'])
        self.assertTrue(service.isActive())
        sleep(40)
        service = registry.listServices(activeOnly=False)[identifier]
        self.assertFalse(service.isActive())
        self.assertTrue(identifier not in registry.listServices())
        registry.updateService(identifier=identifier, type='plein', ipAddress='127.0.0.1', infoport=1234, data={})
        service = registry.listServices()[identifier]
        self.assertEquals(number, service['number'])
        self.assertTrue(service.isActive())
        sleep(80)
        service = registry.listServices(activeOnly=False)[identifier]
        self.assertFalse(service.isActive())
        sleep(24*60*60)
        self.assertTrue(identifier in registry.listServices(activeOnly=False))
        self.assertTrue(registry.listServices(activeOnly=False)[identifier]['longgone'])
        self.assertFalse(registry.listServices(activeOnly=False)[identifier]['readable'])
        self.assertFalse(registry.listServices(activeOnly=False)[identifier]['writable'])

        registry.updateService(identifier=identifier, type='plein', ipAddress='127.0.0.1', infoport=1234, data={})
        self.assertTrue(identifier in registry._services)
        sleep(2*24*60*60)
        self.assertTrue(identifier in registry._services)
        registry.updateService(identifier=str(uuid4()), type='plein', ipAddress='127.0.0.1', infoport=1234, data={})
        self.assertFalse(identifier in registry.listServices())
        self.assertTrue(identifier in registry.listServices(activeOnly=False))
        self.assertTrue(registry.listServices(activeOnly=False)[identifier]['longgone'])

    def testShouldAllowOverrideOptionToDisableUltimateTimeout(self):
        times = [12345678.0]
        registry = ServiceRegistry(stateDir=self.tempdir, reactor=CallTrace(), domainname='zp.example.org', ultimateTimeout=-1)
        observer = CallTrace('observer')
        registry.addObserver(observer)
        def sleep(seconds):
            times[0] += seconds
        registry._now = lambda: times[0]

        identifier = str(uuid4())
        registry.updateService(identifier=identifier, type='plein', ipAddress='127.0.0.1', infoport=1234, data={})
        registry._services[identifier]._now = lambda: times[0]
        service = registry.listServices()[identifier]
        self.assertEquals(times[0], service['lastseen'])
        self.assertTrue(service.isActive())
        sleep(80)
        service = registry.listServices(activeOnly=False)[identifier]
        self.assertFalse(service.isActive())
        sleep(365*24*60*60)
        service = registry.listServices(activeOnly=False)[identifier]
        self.assertFalse(service.isActive())

    def testShouldAddState(self):
        registry = ServiceRegistry(stateDir=self.tempdir, reactor=CallTrace(), domainname='zp.example.org', ultimateTimeout=-1)
        observer = CallTrace('observer')
        registry.addObserver(observer)
        identifier = str(uuid4())
        registry.updateService(identifier=identifier, type='plein', ipAddress='127.0.0.1', infoport=1234, data={})
        service = registry.listServices()[identifier]
        self.assertFalse('state' in service, service)
        service = registry.listServices(includeState=True)[identifier]
        self.assertEquals({'readable': False, 'writable': False}, service['state'])

    def testShouldUpdateDns(self):
        registry = ServiceRegistry(stateDir=self.tempdir, reactor=CallTrace(), domainname='zp.example.org')
        observer = CallTrace('observer')
        registry.addObserver(observer)
        identifier = str(uuid4())
        registry.updateService(identifier=identifier, type='api', ipAddress='127.0.0.1', infoport=1234, data={})

        self.assertEquals(['updateZone'], observer.calledMethodNames())
        method = observer.calledMethods[0]
        self.assertEquals(registry.getService(identifier).fqdn(), method.kwargs['fqdn'])
        self.assertEquals('127.0.0.1', method.kwargs['ipAddress'])

    def testShouldUpdateDnsOnDelete(self):
        times = [12345678.0]
        registry = ServiceRegistry(stateDir=self.tempdir, reactor=CallTrace(), domainname='zp.example.org')
        observer = CallTrace('observer')
        registry.addObserver(observer)
        def sleep(seconds):
            times[0] += seconds
        registry._now = lambda: times[0]

        identifier = str(uuid4())
        registry.updateService(identifier=identifier, type='api', ipAddress='127.0.0.1', infoport=1234, data={})
        self.assertEquals(['updateZone'], observer.calledMethodNames())
        registry.listServices()
        self.assertEquals(['updateZone'], observer.calledMethodNames())
        sleep(2*24*60*60)
        services = registry.listServices()
        self.assertEquals(['updateZone'], observer.calledMethodNames())
        self.assertTrue(identifier not in services, services)

    def testShouldAllowOldRegistryFileFormat(self):
        identifier = str(uuid4())
        with open(join(self.tempdir, 'serviceregistry.json'), 'w') as f:
            f.write("""{"%s": {"type": "kennisbank", "ipAddress": "89.16.161.123", "number": 0, "infoport": 6002, "lastseen": 1}}""" % identifier)
        reqistry = ServiceRegistry(stateDir=self.tempdir, domainname='zp.example.org', reactor=CallTrace())
        self.assertEquals(1, len(reqistry.listServices(activeOnly=False)))

    def testShouldUpdateFlags(self):
        reactor = CallTrace('reactor')
        registry = ServiceRegistry(reactor, self.tempdir, domainname="zp.example.org")
        observer = CallTrace('observer')
        registry.addObserver(observer)

        identifier = str(uuid4())
        registry.updateService(identifier=identifier, type='plein', ipAddress='127.0.0.1', infoport=1234, data={})
        registry = ServiceRegistry(reactor, self.tempdir, domainname="zp.example.org")

        for flagName, flag in SERVICE_FLAGS.items():
            service = registry.listServices().get(identifier)
            self.assertFalse(service[flagName], service)
            state = registry.getPrivateStateFor(identifier)
            self.assertFalse(state[flagName], service)

            reactor.calledMethods.reset()
            registry.setFlag(identifier, flag, True)
            service = registry.listServices().get(identifier)
            self.assertFalse(service[flagName], service)
            state = registry.getPrivateStateFor(identifier)
            self.assertTrue(state[flagName], service)
            registry.updateService(identifier=identifier, type='plein', ipAddress='127.0.0.1', infoport=1234, data={})
            registry = ServiceRegistry(reactor, self.tempdir, domainname="zp.example.org")
            service = registry.listServices().get(identifier)
            state = registry.getPrivateStateFor(identifier)
            self.assertTrue(service[flagName], service)
            self.assertTrue(state[flagName], service)

            reactor.calledMethods.reset()
            registry.setFlag(identifier, flag, False)
            service = registry.listServices().get(identifier)
            state = registry.getPrivateStateFor(identifier)
            self.assertFalse(service[flagName], service)
            self.assertTrue(state[flagName], service)
            self.assertEquals(['addTimer'], reactor.calledMethodNames())
            addTimer = reactor.calledMethods[0]
            self.assertEquals(30, addTimer.args[0])
            addTimer.args[1]()
            registry = ServiceRegistry(reactor, self.tempdir, domainname="zp.example.org")
            service = registry.listServices().get(identifier)
            state = registry.getPrivateStateFor(identifier)
            self.assertFalse(service[flagName], service)
            self.assertFalse(state[flagName], service)

    def testShouldSetFlagImmediate(self):
        i = [0]
        def addTimer(*args, **kwargs):
            i[0] = i[0] + 1
            return i[0]
        reactor = CallTrace('reactor', methods=dict(addTimer=addTimer))
        registry = ServiceRegistry(reactor, self.tempdir, domainname="zp.example.org")
        observer = CallTrace('observer')
        registry.addObserver(observer)

        identifier = str(uuid4())
        registry.updateService(identifier=identifier, type='plein', ipAddress='127.0.0.1', infoport=1234, data={})
        registry = ServiceRegistry(reactor, self.tempdir, domainname="zp.example.org")

        flag = READABLE
        service = registry.getService(identifier)

        registry.setFlag(identifier, flag, True, immediate=True)
        registry.setFlag(identifier, flag, False)
        self.assertEqual(['addTimer'], reactor.calledMethodNames())
        service = registry.getService(identifier)
        self.assertFalse(service[flag.name], service)
        state = registry.getPrivateStateFor(identifier)
        self.assertTrue(state[flag.name], state)
        self.assertFalse(state[flag.name + "_goingup"])

        registry.setFlag(identifier, flag, True, immediate=True)
        self.assertEqual(['addTimer', 'removeTimer'], reactor.calledMethodNames())
        service = registry.getService(identifier)
        self.assertTrue(service[flag.name], service)
        state = registry.getPrivateStateFor(identifier)
        self.assertTrue(state[flag.name], state)
        self.assertFalse(flag.name + "_goingup" in state)

    def testShouldUnsetFlagImmediate(self):
        i = [0]
        def addTimer(*args, **kwargs):
            i[0] = i[0] + 1
            return i[0]

        reactor = CallTrace('reactor', methods=dict(addTimer=addTimer))
        registry = ServiceRegistry(reactor, self.tempdir, domainname="zp.example.org")
        observer = CallTrace('observer')
        registry.addObserver(observer)

        identifier = str(uuid4())
        registry.updateService(identifier=identifier, type='plein', ipAddress='127.0.0.1', infoport=1234, data={})
        registry = ServiceRegistry(reactor, self.tempdir, domainname="zp.example.org")

        flag = READABLE
        service = registry.getService(identifier)

        registry.setFlag(identifier, flag, True)
        self.assertEqual([], reactor.calledMethodNames())
        service = registry.getService(identifier)
        self.assertFalse(service[flag.name], service)
        state = registry.getPrivateStateFor(identifier)
        self.assertTrue(state[flag.name], state)
        self.assertTrue(state[flag.name + "_goingup"])

        registry.setFlag(identifier, flag, False, immediate=True)
        self.assertEqual([], reactor.calledMethodNames())
        service = registry.getService(identifier)
        self.assertFalse(service[flag.name], service)
        state = registry.getPrivateStateFor(identifier)
        self.assertFalse(state[flag.name], state)
        self.assertFalse(flag.name + "_goingup" in state)

    def testShouldUpdateData(self):
        registry = ServiceRegistry(stateDir=self.tempdir, reactor=CallTrace(), domainname="zp.example.org")
        observer = CallTrace('observer')
        registry.addObserver(observer)

        identifier = str(uuid4())
        registry.updateService(identifier=identifier, type='plein', ipAddress='127.0.0.1', infoport=1234, data={'VERSION': '0.1.2.3'})
        service = registry.listServices().get(identifier)
        self.assertEquals({'VERSION': '0.1.2.3'}, service['data'])

        registry.updateService(identifier=identifier, type='plein', ipAddress='127.0.0.1', infoport=1234, data={'error': 1, 'VERSION': '0.1.2.3'})
        service = registry.listServices().get(identifier)
        self.assertEquals({'error': 1, 'VERSION': '0.1.2.3'}, service['data'])

    def testShouldDeleteService(self):
        times = [12345678.0]
        registry = ServiceRegistry(stateDir=self.tempdir, reactor=CallTrace(), domainname='zp.example.org')
        observer = CallTrace('observer')
        registry.addObserver(observer)
        def sleep(seconds):
            times[0] += seconds
        registry._now = lambda: times[0]

        identifier = str(uuid4())
        registry.updateService(identifier=identifier, type='api', ipAddress='127.0.0.1', infoport=1234, data={})
        fqdn = registry.getService(identifier).fqdn()
        self.assertEquals(['updateZone'], observer.calledMethodNames())
        sleep(2*24*60*60)
        registry.listServices()
        self.assertEquals(['updateZone'], observer.calledMethodNames())
        registry.deleteService(identifier)
        self.assertEquals(['updateZone', 'deleteFromZone'], observer.calledMethodNames())
        self.assertEquals({'fqdn': fqdn}, observer.calledMethods[-1].kwargs)
        self.assertFalse(identifier in registry.listServices(activeOnly=False))
        registry = ServiceRegistry(stateDir=self.tempdir, reactor=CallTrace(), domainname='zp.example.org')
        self.assertFalse(identifier in registry.listServices(activeOnly=False))

    def testShouldReEnableService(self):
        times = [12345678.0]
        registry = ServiceRegistry(stateDir=self.tempdir, reactor=CallTrace(), domainname='zp.example.org')
        observer = CallTrace('observer')
        registry.addObserver(observer)
        def sleep(seconds):
            times[0] += seconds
        registry._now = lambda: times[0]

        identifier = str(uuid4())
        registry.updateService(identifier=identifier, type='api', ipAddress='127.0.0.1', infoport=1234, data={})
        registry._services[identifier]._now = lambda: times[0]
        sleep(2*24*60*60)
        self.assertTrue(registry.listServices(activeOnly=False)[identifier]['longgone'])
        registry.updateService(identifier=identifier, type='api', ipAddress='127.0.0.1', infoport=1234, data={})
        registry._services[identifier]._now = lambda: times[0]
        self.assertTrue(registry.listServices(activeOnly=False)[identifier]['longgone'])
        registry.reEnableService(identifier)
        self.assertFalse('longgone' in registry.listServices(activeOnly=False)[identifier])

    def testShouldNotSetFlagsIfTooLongGone(self):
        times = [12345678.0]
        registry = ServiceRegistry(stateDir=self.tempdir, reactor=CallTrace(), domainname='zp.example.org')
        observer = CallTrace('observer')
        registry.addObserver(observer)
        def sleep(seconds):
            times[0] += seconds
        registry._now = lambda: times[0]
        identifier = str(uuid4())
        registry.updateService(identifier=identifier, type='api', ipAddress='127.0.0.1', infoport=1234, data={})
        sleep(2*24*60*60)
        self.assertTrue(registry.listServices(activeOnly=False)[identifier]['longgone'])
        self.assertFalse(registry.listServices(activeOnly=False)[identifier]['readable'])

        registry.updateService(identifier=identifier, type='api', ipAddress='127.0.0.1', infoport=1234, data={})
        self.assertRaises(ValueError, lambda: registry.setFlag(identifier, READABLE, True))
        self.assertTrue(registry.listServices(activeOnly=False)[identifier]['longgone'])
        self.assertFalse(registry.listServices(activeOnly=False)[identifier]['readable'])

    def testGetStateForNoneExistingService(self):
        registry = ServiceRegistry(stateDir=self.tempdir, reactor=CallTrace(), domainname='zp.example.org')
        self.assertEquals(None, registry.getPrivateStateFor(identifier='ehh'))

    def testKeepDownServicesForAWhile(self):
        added_time = [0]
        def currentTime():
            return time() + added_time[0]
        def createRegistry():
            r = ServiceRegistry(
                    stateDir=self.tempdir,
                    domainname='zp.example.org',
                    serviceTimeout=30,
                    ultimateTimeout=24*60*60,
                    retainAfterStartupTimeout=60,
                    reactor=CallTrace(),
                )
            observer = CallTrace('observer')
            r.addObserver(observer)
            r._now = currentTime
            r._startUpTime = currentTime()
            return r
        # T = 0
        registry = createRegistry()
        id1, id2, id3 = (str(uuid4()) for i in xrange(3))
        registry.updateService(identifier=id1, type='type_one', ipAddress='127.0.0.1', infoport=1234, data={})
        registry._services[id1]._now = currentTime

        # T = 40
        added_time[0] += 40
        registry.updateService(identifier=id2, type='type_two', ipAddress='127.0.0.1', infoport=1234, data={})
        registry._services[id2]._now = currentTime
        registry.updateService(identifier=id3, type='type_three', ipAddress='127.0.0.1', infoport=1234, data={})
        registry._services[id3]._now = currentTime
        self.assertEquals(set(['type_two', 'type_three']), set(d['type'] for d in registry.listServices().values()))
        # T = 40 for registry file
        filetimes = stat(join(self.tempdir, SERVICEREGISTRY_FILE))
        utime(join(self.tempdir, SERVICEREGISTRY_FILE), (filetimes.st_atime + 40, filetimes.st_mtime + 40))

        # T = 80
        added_time[0] += 40
        registry = createRegistry()
        for s in registry._services.values():
            s._now = currentTime
        self.assertEquals(set(['type_two', 'type_three']), set(d['type'] for d in registry.listServices().values()))
        # T = 130
        added_time[0] += 50
        registry.updateService(identifier=id3, type='type_three', ipAddress='127.0.0.1', infoport=1234, data={})
        self.assertEquals(set(['type_two', 'type_three']), set(d['type'] for d in registry.listServices().values()))
        # T = 155
        added_time[0] += 25
        self.assertEquals(set(['type_three']), set(d['type'] for d in registry.listServices().values()))

    def testServiceRegistryOldFormat(self):
        uuid1 = str(uuid4())
        uuid2 = str(uuid4())
        with open(join(self.tempdir, 'serviceregistry.json'), 'w') as f:
            d = JsonDict({
                    uuid1: {
                        "ipAddress": "5.153.228.85",
                        "readable": True,
                        "number": 1,
                        "data": {
                            "uptime": 366867,
                            "VERSION": "1.5.12.3"
                        },
                        "writable": True,
                        "lastseen": 1423494771.904539,
                        "type": "holding",
                        "infoport": 35609,
                    },
                    uuid2: {
                        "ipAddress": "5.153.228.85",
                        "readable": True,
                        "number": 1,
                        "data": {
                            "uptime": 366867,
                            "VERSION": "1.5.12.3"
                        },
                        "writable": True,
                        "lastseen": 1423494771.904539,
                        "type": "plein",
                        "infoport": 41609,
                    }
                })
            d.dump(f)
        registry = ServiceRegistry(
            stateDir=self.tempdir,
            domainname='zp.example.org',
            reactor=CallTrace(),
        )
        self.assertEquals(set([uuid1, uuid2]), set(registry.listServices(activeOnly=False).keys()))

    def testUpdateScriptAsService(self):
        times = [12345678.0]
        registry = ServiceRegistry(stateDir=self.tempdir, reactor=CallTrace(), domainname='zp.example.org')
        observer = CallTrace('observer')
        registry.addObserver(observer)
        self.assertEquals(60, registry._timeout)
        def sleep(seconds):
            times[0] += seconds
        registry._now = lambda: times[0]

        identifier = str(uuid4())
        registry.updateService(identifier=identifier, type='script', ipAddress='127.0.0.1', infoport=0, data={'updateInterval': 3600})
        self.assertTrue(registry.getService(identifier).isActive())
        sleep(59)
        self.assertTrue(registry.getService(identifier).isActive())
        sleep(2)
        self.assertTrue(registry.getService(identifier).isActive())
        sleep(1200)
        self.assertTrue(registry.getService(identifier).isActive())
        sleep(3600)
        self.assertTrue(registry.getService(identifier).isActive())
        sleep(3600)
        self.assertFalse(registry.getService(identifier).isActive())
