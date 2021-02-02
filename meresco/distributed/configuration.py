## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2012-2015, 2019, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015, 2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2021 SURF https://www.surf.nl
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

from meresco.core import Observable

from meresco.components.json import JsonDict
from os.path import isdir, join, isfile
from os import makedirs, rename
from shutil import rmtree

class Configuration(Observable):
    def __init__(self, stateDir, name=None, defaultConfig=None):
        Observable.__init__(self, name=name)
        isdir(stateDir) or makedirs(stateDir)
        self._configFile = join(stateDir, 'config.json')
        if isfile(join(stateDir, 'configuration', 'config.json', 'config')):
            rename(join(stateDir, 'configuration', 'config.json', 'config'), self._configFile)
            rmtree(join(stateDir, 'configuration'))
        if not isfile(self._configFile):
            self._save(defaultConfig or {})

    def getConfig(self):
        return JsonDict.load(self._configFile)

    def saveConfig(self, config):
        self._save(config)
        yield self.all.updateConfig(config=config)

    def _save(self, config):
        JsonDict(config).dump(self._configFile)

    def observer_init(self):
        yield self.all.updateConfig(config=self.getConfig())

class UpdatableConfig(Observable):
    "Caches configuration, can be used to retrieve config."
    def __init__(self, **kwargs):
        Observable.__init__(self, **kwargs)
        self._config = dict()

    def updateConfig(self, config, **kwargs):
        self._config = config
        return
        yield

    def get(self, *args, **kwargs):
        return self._config.get(*args, **kwargs)

    def __getitem__(self, *args, **kwargs):
        return self._config.__getitem__(*args, **kwargs)



