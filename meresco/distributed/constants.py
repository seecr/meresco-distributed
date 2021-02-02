## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015-2016, 2021 Seecr (Seek You Too B.V.) https://seecr.nl
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

SERVICE_TIMEOUT = 60
ULTIMATE_TIMEOUT = 24*60*60
RETAIN_AFTER_STARTUP_TIMEOUT = 60 + 30

SERVICE_POLL_INTERVAL = SERVICE_TIMEOUT / 2
ADMIN_DOWNLOAD_PERIOD_CONFIG_KEY = 'debug.global.adminDownload.period'
OAI_DOWNLOAD_PERIOD_CONFIG_KEY = 'debug.global.oaiDownload.period'
OAI_DOWNLOAD_INTERVAL = 0.1
PERIODIC_DOWNLOAD_RETRY_AFTER_ERROR_CONFIG_KEY = 'debug.global.periodicDownload.retryAfterErrorTime'
PERIODIC_DOWNLOAD_RETRY_AFTER_ERROR_TIME = 30

from ._serviceflags import READABLE, WRITABLE, SERVICE_FLAGS, READWRITE
