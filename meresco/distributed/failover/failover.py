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

from .__version__ import VERSION
from time import sleep
from meresco.components import ParseArguments
from meresco.distributed import ConfigDownloadProcessor
from meresco.distributed.constants import SERVICE_POLL_INTERVAL
from urllib2 import HTTPError
from os import system
from seecr.utils import isRootUser
from ._utils import log

defaultNginxReloadCmd = 'svc -h /etc/service/nginx'

class Failover(object):
    def __init__(self):
        self._nginxConfigurations = []

    def addConfiguration(self, config):
        self._nginxConfigurations.append(config)

    def main(self, sharedSecret, adminHostname, adminPort, name, nginxReload=defaultNginxReloadCmd, verbose=True, **ignored):
        if nginxReload == defaultNginxReloadCmd and not isRootUser():
            raise ValueError('Run as rootuser for default nginx restart script.')

        configDownloadProcessor = ConfigDownloadProcessor.forUpdate(
                identifier="nginx-failover{0}".format(('-'+name) if name else ''),
                type="nginx-failover",
                infoport=0,
                statePath=None,
                keys=[],
                version=VERSION,
                sharedSecret=sharedSecret,
                updateInterval=SERVICE_POLL_INTERVAL
            )
        try:
            configAndServices = configDownloadProcessor.downloadAndUpdate(adminHostname, adminPort)
        except HTTPError:
            # Some older meresco-distributed versions cannot accept updates from scripts.
            configAndServices = configDownloadProcessor.download(adminHostname, adminPort)

        mustUpdate = False
        sleeptime = 3600
        for nginxConfiguration in self._nginxConfigurations:
            result = nginxConfiguration.update(verbose=True, **configAndServices)
            mustUpdate = mustUpdate or result.mustUpdate
            sleeptime = min(sleeptime, result.sleeptime)
        if mustUpdate:
            system(nginxReload)
        if verbose:
            log('Sleeping: {0}s\n'.format(sleeptime))
        sleep(sleeptime)


    def mainWithParseArguments(self):
        parser = ParseArguments()
        parser.addOption('', '--adminHostname', help='Admin hostname', mandatory=True)
        parser.addOption('', '--adminPort', help='Admin port', default=10000, type='int')
        parser.addOption('-q', '--quiet', help="Disable apache logging.", action="store_false", default=True, dest="verbose")
        parser.addOption('-n', '--name', default='', help='Service name, defaults to ""')
        parser.addOption('', '--nginxReload', type='str', help='The command to reload nginx (default: "{default}")', default=defaultNginxReloadCmd)
        parser.addOption('', '--sharedSecret', help='Shared secret for updating as a service in admin', mandatory=True)
        options, args = parser.parse()
        return self.main(**vars(options))