#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2009, NexR (http://nexr.co.kr)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os.path, os, re, sys
from twisted.web2 import log, wsgi, resource
from twisted.internet import reactor

def make_wsgi(request):
    os.environ['PATH_INFO'] = request.path  # for basehttp module
    os.environ['SCRIPT_URL'] = request.path # for correct url routing
    from django.core.handlers.wsgi import WSGIHandler
    from django.core.servers.basehttp import AdminMediaHandler
    return wsgi.WSGIResource(AdminMediaHandler(WSGIHandler()))

class ArbitrarySettingsDecide(resource.Resource):
    addSlash = True

    def locateChild(self, request, segments):
        return self, ()

    def renderHTTP(self, request):
        return make_wsgi(request)

if __name__ == '__builtin__':
    from twisted.application import service, strports
    from twisted.web2 import server, vhost, channel
    from twisted.python import util

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'opencourselabs.settings'

    test_site = ArbitrarySettingsDecide()
    res = log.LogWrapperResource(test_site)
    log.DefaultCommonAccessLoggingObserver().start()

    # Create the site and application objects
    site = server.Site(res)
    application = service.Application("Twisted-CCIU")

    from django.conf import settings

    # Serve it via standard HTTP on port 8081
    s = strports.service('tcp:%d' % settings.TWISTED_PORT, channel.HTTPFactory(site))
    s.setServiceParent(application)
