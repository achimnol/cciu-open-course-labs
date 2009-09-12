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


from functools import wraps
from django.conf import settings
from django.http import QueryDict
from django.utils.importlib import import_module

def session_from_http_params(view_func):
    @wraps(view_func)
    def decorated(request, *args, **kwargs):
        engine = import_module(settings.SESSION_ENGINE)
        session_key = request.GET.get(settings.SESSION_COOKIE_NAME, None)
        if session_key is None:
            session_key = request.POST.get(settings.SESSION_COOKIE_NAME, None)
        request.session = engine.SessionStore(session_key)        
        return view_func(request, *args, **kwargs)
    return decorated

def persistent_params(*param_names):
    def decorate(view_func):
        @wraps(view_func)
        def decorated(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            if response.status_code / 100 == 3:
                location = response['Location']
                parts = location.split('?')
                if len(parts) == 1:
                    query_dict = QueryDict('', mutable=True)
                else:
                    query_dict = QueryDict(parts[1], mutable=True)
                for name in param_names:
                    value = request.GET.get(name, None)
                    # If a parameter does not exist, don't add it.
                    if value is not None:
                        query_dict[name] = value
                new_query_string = query_dict.urlencode() 
                response['Location'] = parts[0] + '?' + new_query_string
            return response
        return decorated
    return decorate
