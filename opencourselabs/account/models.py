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

"""
Account models.

Row-level permission system is hired from jazzgoth's work here:
http://code.google.com/p/django-granular-permissions/
"""

from datetime import datetime
from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.sites.models import Site
from django.contrib.flatpages.models import FlatPage

class UserProfile(models.Model):
    user = models.OneToOneField('auth.User')
    real_name = models.CharField(max_length=30)
    organization = models.CharField(max_length=60)

    def __unicode__(self):
        return u'%s@%s' % (self.real_name, self.organization)

class RegisterRequest(models.Model):
    key = models.CharField(max_length=32, unique=True)
    real_name = models.CharField(max_length=30, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(default=datetime.now)

    # We don't restrict organization in models, but its inputs are restricted by forms.
    organization = models.CharField(max_length=60)

    def __unicode__(self):
        return u'%s@%s: %s' % (self.real_name, self.organization, self.email)

    class Meta:
        verbose_name = 'User Registration Request'

class Permission(models.Model):
    name = models.CharField(max_length=16)
    content_type = models.ForeignKey(ContentType, related_name="row_permissions")
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User, related_name='row_permission_set', null=True, blank=True)
    group = models.ForeignKey(Group, related_name='row_permission_set', null=True, blank=True)
 
    def __unicode__(self):
        return u"%s | %s | %d | %s" % (self.content_type.app_label, self.content_type, self.object_id, self.name)
 
    class Meta:
        verbose_name = 'permission'
        verbose_name_plural = 'permissions'

