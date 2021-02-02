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

from urllib.parse import parse_qs
from meresco.components.json import JsonDict

from meresco.core import Observable
from meresco.components.http.utils import CRLF, redirectHttp

class ConfigHandler(Observable):
    def __init__(self, name=None):
        Observable.__init__(self, name=name)
        self._actions = {
            'update': self.handleUpdate,
        }

    def handleRequest(self, path, Method, **kwargs):
        prefix, action = path.rsplit('/', 1)
        if Method != 'POST':
            yield 'HTTP/1.0 405 Method Not Allowed' + CRLF*2
            return
        if action not in self._actions:
            yield 'HTTP/1.0 400 Bad Request' + CRLF*2
            return
        yield self._actions[action](**kwargs)

    def handleUpdate(self, Body, session, **kwargs):
        formValues = parse_qs(Body, keep_blank_values=True)
        redirectUrl = formValues.get('redirectUrl')[0]
        try:
            config = JsonDict.loads(formValues.get('config')[0])
            for config_key in sorted(k for k in formValues.keys() if k.startswith('config_')):
                config.update(JsonDict.loads(formValues.get(config_key)[0]))
            yield self.all.saveConfig(config=config)
            session['message'] = {'class': 'success', 'text': 'Configuratie opgeslagen.'}
        except ValueError:
            session['message'] = {'class': 'error', 'text': "Ongeldige JSON"}
        yield redirectHttp % redirectUrl

