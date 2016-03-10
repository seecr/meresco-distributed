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

from os import makedirs
from os.path import join, abspath, isfile, isdir
from urllib import urlencode
from urllib2 import urlopen, HTTPError, URLError
from socket import timeout
import sys

from meresco.components.http.utils import createHttpHeaders
from meresco.core import Observable

from .utils import serviceUpdateHash, IP_ADDRESS
from meresco.components.json import JsonDict
from copy import copy
from simplejson import dumps

from time import time

class ConfigDownloadProcessor(Observable):
    apiVersion = 2

    def __init__(self, statePath, version, keys=None, _bodyArgs=None, syncDownloadTimeout=15, forUpdate=True, name=None, identifier=None, type=None, additionalArguments=None, **data):
        Observable.__init__(self, name=name)
        self._version = version
        self._originalArguments = dict(statePath=statePath, keys=keys, _bodyArgs=_bodyArgs, syncDownloadTimeout=syncDownloadTimeout, forUpdate=forUpdate, name=name, identifier=identifier, type=type, version=version, additionalArguments=additionalArguments, **data)
        self._starttime = time()
        self._syncDownloadTimeout = syncDownloadTimeout
        self._bodyArgs = _bodyArgs
        self._identifier = identifier
        self._type = type
        self._moreData = data
        self._keys = '' if keys is None else ','.join(sorted(keys))
        self._cache = _NoCache() if statePath is None else _Cache(statePath)
        self._forUpdate = forUpdate
        self._additionalArguments = dict() if additionalArguments is None else additionalArguments

    @classmethod
    def forUpdate(cls, identifier, type, infoport, statePath, sharedSecret, ipAddress=None, **kwargs):
        ipAddress = IP_ADDRESS if ipAddress is None else ipAddress
        _bodyArgs = {
            'identifier': identifier,
            'type': type,
            'ipAddress': ipAddress,
            'infoport': infoport,
            'hash': serviceUpdateHash(secret=sharedSecret, identifier=identifier, type=type, ipAddress=ipAddress, infoport=infoport),
        }
        return cls(statePath=statePath, _bodyArgs=_bodyArgs, forUpdate=True, identifier=identifier, type=type, **kwargs)

    @classmethod
    def forDownload(cls, statePath=None, **kwargs):
        return cls(statePath=statePath, forUpdate=False, **kwargs)

    def copy(self, **kwargs):
        arguments = dict(**self._originalArguments)
        arguments.update(**kwargs)
        return ConfigDownloadProcessor(**arguments)

    def _downloadPathAndArgs(self, forUpdate=None):
        forUpdate = forUpdate if forUpdate is not None else self._forUpdate
        args = dict(keys=self._keys)
        if self._identifier and not forUpdate:
            args['identifier'] = self._identifier
        args.update(self._additionalArguments)
        return '/api/service/v{apiVersion}/{0}?{arguments}'.format(
                "update" if forUpdate and self._forUpdate else "list",
                arguments=urlencode(sorted(args.items())),
                apiVersion=self.apiVersion,
            )

    def buildRequest(self, additionalHeaders=None):
        moreHeaders =  createHttpHeaders(additionalHeaders, userAgent=createUserAgent(type=self._type, identifier=self._identifier, version=self._version))
        if not self._forUpdate:
            return """GET {path} HTTP/1.0{moreHeaders}\r\n\r\n""".format(
                    path=self._downloadPathAndArgs(),
                    moreHeaders=moreHeaders,
                )
        postData = self._postArguments()
        arguments = dict(keys=self._keys)
        arguments.update(self._additionalArguments)
        return """POST {path} HTTP/1.0\r\nContent-Length: {length}{moreHeaders}\r\n\r\n{postData}""".format(
            path=self._downloadPathAndArgs(forUpdate=True),
            length=len(postData),
            moreHeaders=moreHeaders,
            postData=postData)

    def _postArguments(self):
        arguments = copy(self._bodyArgs) or {'data': None}
        dataDict = self._createDefaultData()
        self.do.serviceData(dataDict)
        if dataDict:
            arguments['data'] = dumps(dataDict)
        return urlencode(sorted(arguments.items()))

    def _createDefaultData(self):
        return dict(VERSION=self._version, uptime=int(time() - self._starttime), **self._moreData)

    def handle(self, data):
        d = JsonDict.loads(data)
        self._cache.update(configuration=d)
        yield self.updateConfig(**d)

    def downloadAndUpdate(self, adminHostname, adminPort):
        adminUrl = "http://{0}:{1}{path}".format(
                adminHostname,
                adminPort,
                path=self._downloadPathAndArgs(forUpdate=True),
            )
        return self._download(adminUrl, timeout=self._syncDownloadTimeout, data=self._postArguments())

    def download(self, adminHostname, adminPort):
        adminUrl = "http://{0}:{1}{path}".format(
                adminHostname,
                adminPort,
                path=self._downloadPathAndArgs(forUpdate=False),
            )
        return self._download(url=adminUrl, timeout=self._syncDownloadTimeout)

    def _download(self, url, **kwargs):
        try:
            configuration = JsonDict.load(urlopen(url, **kwargs))
            self._cache.update(configuration)
        except (HTTPError, URLError, timeout), e:
            sys.stderr.write("""%s (%s).
Tried: %s
-----
""" % (e.__class__.__name__, str(e), url))
            configuration = self._cache.retrieve()
            if configuration is None:
                sys.stderr.write('%s: configuration cachefile "%s" not found!\n' % (self.__class__.__name__, self._cache.filepath))
                sys.stderr.flush()
                raise
            sys.stderr.write('%s: configuration cachefile "%s" found.\n' % (self.__class__.__name__, self._cache.filepath))
            sys.stderr.flush()
        return configuration

    def updateConfig(self, **kwargs):
        yield self.all.updateConfig(**kwargs)

class _Cache(object):
    def __init__(self, statePath):
        if not isdir(statePath):
            makedirs(statePath)
        self.filepath = abspath(join(statePath, 'configuration_cache.json'))

    def update(self, configuration):
        configuration.dump(self.filepath, indent=4, sort_keys=True)

    def retrieve(self):
        if not isfile(self.filepath):
            return None
        return JsonDict().load(self.filepath)

class _NoCache(object):
    filepath = None
    def update(self, configuration):
        pass

    def retrieve(self):
        return None

def createUserAgent(type=None, identifier=None, version=None):
    return ' '.join([
            type or 'Unknown',
            identifier or '_',
            'v%s' % (version or '?'),
        ])
