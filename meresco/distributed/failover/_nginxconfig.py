## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2016 SURFmarket https://surf.nl
# Copyright (C) 2016-2018 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2018 Stichting Kennisnet https://www.kennisnet.nl
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

from weightless.core import asString
from meresco.core import Observable
from meresco.distributed.constants import ADMIN_DOWNLOAD_PERIOD_CONFIG_KEY, SERVICE_POLL_INTERVAL
from meresco.distributed.utils import usrSharePath as defaultUsrSharePath
from os.path import join, isfile
from ._utils import log, noLog, UpdateResult
from escaping import escapeFilename

class _NginxConfig(Observable):
    def __init__(self, nginxConfigFile, usrSharePath=None, name=None, **kwargs):
        Observable.__init__(self, **kwargs)
        self._nginxConfigFile = nginxConfigFile.format(name=name if name is None else escapeFilename(name))
        self._usrSharePath = join(defaultUsrSharePath, 'failover') if usrSharePath is None else usrSharePath

    def update(self, config, verbose=True, **kwargs):
        sleeptime = config.get(ADMIN_DOWNLOAD_PERIOD_CONFIG_KEY, SERVICE_POLL_INTERVAL)
        newConfig = self.generate(config=config, verbose=verbose, **kwargs)
        _log = log if verbose else noLog
        mustUpdate = False
        if not isfile(self._nginxConfigFile) or newConfig != open(self._nginxConfigFile).read():
            with open(self._nginxConfigFile, 'w') as fd:
                fd.write(newConfig)
            mustUpdate = True
        _log("Config in {0}. Must update: {1}\n".format(repr(self._nginxConfigFile), mustUpdate))
        return UpdateResult(mustUpdate, sleeptime)

    def generate(self, **kwargs):
        return asString(self._generate(**kwargs))
