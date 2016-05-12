## begin license ##
#
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  a project of the Koninklijke Bibliotheek
#  and provides a search service for all public
#  libraries in the Netherlands.
#
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
#
# This file is part of "NBC+ (Zoekplatform BNL)"
#
# "NBC+ (Zoekplatform BNL)" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "NBC+ (Zoekplatform BNL)" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "NBC+ (Zoekplatform BNL)"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from os import makedirs
from os.path import join, isfile, isdir
from meresco.components.json import JsonDict
from meresco.html import PostActions
from urlparse import parse_qs
from meresco.components.http.utils import Ok, CRLF

class Remarks(PostActions):
    def __init__(self, stateDir, **kwargs):
        super(Remarks, self).__init__(**kwargs)
        isdir(stateDir) or makedirs(stateDir)
        self._filePath = join(stateDir, REMARKS_FILENAME)
        self._remarks = self._load()
        self.registerAction('save', self.handleSave)

    def handleSave(self, Body, **kwargs):
        formValues = parse_qs(Body)
        key = formValues['key'][0]
        contents = formValues.get('contents', [''])[0]
        if not contents:
            self._remarks.pop(key, None)
        else:
            self._remarks[key] = contents
        self._save()
        yield Ok + CRLF * 2

    def getRemarks(self, key):
        return self._remarks.get(key, '')

    def _load(self):
        if not isfile(self._filePath):
            return {}
        return JsonDict.load(self._filePath)

    def _save(self):
        JsonDict(self._remarks).dump(self._filePath)

REMARKS_FILENAME = 'remarks.json'
