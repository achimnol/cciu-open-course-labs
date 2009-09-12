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


import os, tempfile
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404
from opencourselabs.labsite.decorators import labsite_context, team_context, labsite_perm_required
from opencourselabs.utils import respond_as_json
from opencourselabs.utils.decorators import session_from_http_params
from .models import UploadTempFile

@login_required
@labsite_context
@team_context
def index(request, labsite, user_team):
    pass

@session_from_http_params
@login_required
def temp_upload(request, action):
    key = request.GET['key']
    try:
        original_name = request.GET['filename']
    except KeyError:
        # "Filedata" is the reserved name by SWFUpload.
        try:
            original_name = request.FILES['Filedata'].name
        except KeyError:
            original_name = None

    if action == 'save':
        if request.method != 'POST':
            return HttpResponseBadRequest('Only POST method is allowed.')
        if original_name is None:
            return HttpResopnseBadRequest('Missing parameters.')

        file = request.FILES['Filedata']
        try:
            fd, temp_path = tempfile.mkstemp('-cciu-uploadtemp')
            destination = os.fdopen(fd, 'wb+')
            for chunk in file.chunks():
                destination.write(chunk)
            destination.close()
        except IOError, e:
            return HttpResponseServerError(repr(e))

        o = UploadTempFile()
        o.key = key
        o.original_name = original_name
        o.saved_path = temp_path
        o.save()

    elif action == 'remove':

        o = get_object_or_404(UploadTempFile, key=key)
        os.remove(o.saved_path)
        o.delete()

    else:
        return HttpResponseBadRequest('Server could not understand the request.')

    result = {
        'success': True,
    }
    return respond_as_json(request, result)
