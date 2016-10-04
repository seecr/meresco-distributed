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

class SslConfig(object):
    def __init__(self, certificate, key):
        self._sslKey = key
        self._sslCertificate = certificate

    def sslLines(self):
        yield """
    ssl on;

    ssl_certificate         {crt};
    ssl_certificate_key     {pem};
    ssl_protocols           TLSv1 TLSv1.1 TLSv1.2;
    keepalive_timeout       60;
    ssl_session_cache       shared:SSL:10m;

    proxy_redirect          http:// https://;
""".format(crt=self._sslCertificate, pem=self._sslKey)