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
from opencourselabs.labsite.models import Labsite, Team
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

# Decorator functions for common labsite instnace handling and permission check.

def labsite_context(view_func):
    @wraps(view_func)
    def decorated(request, url_key, *args, **kwargs):
        labsite = get_object_or_404(Labsite, url_key=url_key)
        return view_func(request, labsite, *args, **kwargs)
    return decorated

def team_context(view_func):
    @wraps(view_func)
    def decorated(request, labsite, *args, **kwargs):
        try:
            if not request.user.is_authenticated():
                user_team = None
            else:
                user_team = Team.objects.get(belongs_to=labsite, members=request.user)
        except Team.DoesNotExist:
            user_team = None
        return view_func(request, labsite, user_team, *args, **kwargs)
    return decorated

def labsite_perm_required(*perm_names):
    def decorate(view_func):
        @wraps(view_func)
        @labsite_context
        def decorated(request, labsite, *args, **kwargs):
            for perm_name in perm_names:
                if request.user.has_row_perm(labsite, perm_name):
                	break
            else:
                raise PermissionDenied()
            return view_func(request, labsite, *args, **kwargs)
        return decorated
    return decorate

