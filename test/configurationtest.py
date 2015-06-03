## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2013, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from weightless.core import compose, be, consume
from meresco.core import Observable

from seecr.test import SeecrTestCase, CallTrace

from meresco.distributed import Configuration
from os.path import join, isdir
from os import makedirs
from meresco.components.json import JsonDict


class ConfigurationTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.configuration = Configuration(self.tempdir)
        self.observer = CallTrace('observer',
                emptyGeneratorMethods='updateConfig',
                ignoredAttributes=['add', 'all_unknown', 'observer_init'])
        self.observable = be(
            (Observable(),
                (self.configuration,
                    (self.observer,),
                )
            ))

    def testShouldReturnEmpty(self):
        self.assertEquals({}, self.configuration.getConfig())

    def testShouldStoreAddedConfiguration(self):
        consume(self.observable.all.saveConfig(CONFIG))
        self.assertEquals(CONFIG, self.configuration.getConfig())

        consume(self.observable.all.saveConfig(config={"anotherPort": 8001}))
        self.assertEquals({'anotherPort': 8001}, self.configuration.getConfig())
        self.assertEquals(['updateConfig', 'updateConfig'], [m.name for m in self.observer.calledMethods])
        self.assertEquals({'anotherPort': 8001}, self.observer.calledMethods[-1].kwargs['config'])

    def testShouldUpdateConfigurationOnObserverInit(self):
        consume(self.observable.all.saveConfig(CONFIG))
        list(compose(self.observable.once.observer_init()))
        self.assertEquals(CONFIG, self.configuration.getConfig())
        self.assertEquals(['updateConfig', 'updateConfig'], [m.name for m in self.observer.calledMethods])
        self.assertEquals(CONFIG, self.observer.calledMethods[-1].kwargs['config'])

    def testShouldUseDefaultConfigurationIfNotPresent(self):
        configuration = Configuration(stateDir=join(self.tempdir, 'sub'), defaultConfig={'a': 1})
        self.observable = be(
            (Observable(),
                (configuration,
                    (self.observer,),
                )
            ))
        list(compose(self.observable.once.observer_init()))
        self.assertEquals({'a': 1}, configuration.getConfig())

        makedirs(join(self.tempdir, 'yes'))
        JsonDict(CONFIG).dump(open(join(self.tempdir, 'yes', 'config.json'), 'w'))
        configuration = Configuration(stateDir=join(self.tempdir, 'yes'), defaultConfig={'a': 1})
        self.assertEquals(CONFIG, configuration.getConfig())

    def testConversion(self):
        makedirs(join(self.tempdir, 'configuration', 'config.json'))
        JsonDict(CONFIG).dump(open(join(self.tempdir, 'configuration', 'config.json', 'config'), 'w'))
        configuration = Configuration(stateDir=self.tempdir, defaultConfig={'a': 1})
        self.assertEquals(CONFIG, configuration.getConfig())
        self.assertFalse(isdir(join(self.tempdir, 'configuration')))


CONFIG = {"port": 8000, "hostname": "localhost"}

