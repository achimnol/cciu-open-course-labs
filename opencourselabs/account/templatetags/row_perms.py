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

from django import template
from django.contrib.auth.models import User

register = template.Library()

class HasRowPermNode(template.Node):
    def __init__(self, user, labsite, perm, varname):
        self.user = template.Variable(user)
        self.labsite = template.Variable(labsite)
        self.perm = perm
        self.varname = varname

    def __repr__(self):
        return '<HasRowPerm node>'

    def render(self, context):
        user = self.user.resolve(context)
        labsite = self.labsite.resolve(context)
        context[self.varname] = user.has_row_perm(labsite, self.perm)
        return ''

def _check_quoted(string):
    return string[0] == '"' and string[-1] == '"'

@register.tag('has_row_perm')
def do_has_row_perm(parser, token):
    """
    A has-row-perm boolean indicator tag for django templates.

    Example usage:
        {% has_row_perm user object "staff" as some_var %}
        {% if some_var %}
        ...
        {% endif %}
    """

    try:
        tokens = token.split_contents()
        tag_name = tokens[0]
        args = tokens[1:]
    except ValueError, IndexError:
        raise template.TemplateSyntaxError('%r tag requires arguments.' % tag_name)

    if _check_quoted(args[0]) or _check_quoted(args[1]) or not _check_quoted(args[2]) \
    	or args[3] != 'as' or _check_quoted(args[4]):
    	raise template.TemplateSyntaxError('%r tag had invalid argument.' % tag_name)

    return HasRowPermNode(args[0], args[1], args[2][1:-1], args[4])

