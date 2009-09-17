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
Account main module.

This row-level permission extension is come from jazzgoth's work here:
http://code.google.com/p/django-granular-permissions/
"""
import new
import inspect
from django.contrib.auth.models import User, AnonymousUser, Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Manager
from opencourselabs.account.models import Permission

class ClassExtenderType(type):
    def __new__(self, classname, classbases, classdict):
        try:
            frame = inspect.currentframe()
            frame = frame.f_back
            if frame.f_locals.has_key(classname):
                old_class = frame.f_locals.get(classname)
                for name,func in classdict.items():
                    setattr(old_class, name, func)
                return old_class
            return type.__new__(self, classname, classbases, classdict)
        finally:
            del frame

class User(object):
    __metaclass__ = ClassExtenderType

    def add_row_perm(self, instance, perm):
        if self.has_row_perm(instance, perm, True):
            return False
        permission = Permission()
        permission.content_object = instance
        permission.user = self
        permission.name = perm
        permission.save()
        return True
        
    def del_row_perm(self, instance, perm):
        if not self.has_row_perm(instance, perm, True):
            return False
        content_type = ContentType.objects.get_for_model(instance)
        objects = Permission.objects.filter(user=self, content_type__pk=content_type.id, object_id=instance.id, name=perm)
        objects.delete()
        return True
        
    def has_row_perm(self, instance, perm, only_me=False):
        if self.is_superuser:
            return True
        if not self.is_active:
            return False

        content_type = ContentType.objects.get_for_model(instance)
        objects = Permission.objects.filter(user=self, content_type__pk=content_type.id, object_id=instance.id, name=perm)
        if objects.count()>0:
            return True
            
        # check groups
        if not only_me:
            for group in self.groups.all():
                if group.has_row_perm(instance, perm):
                    return True
        return False
        
    def get_rows_with_permission(self, instance, perm):
        content_type = ContentType.objects.get_for_model(instance)
        if isinstance(perm, list):
            perm_condition = {'name__in': perm}
        else:
            perm_condition = {'name__exact': perm}
        objects = Permission.objects.filter(Q(user=self) | Q(group__in=self.groups.all()), content_type__pk=content_type.id, **perm_condition)
        return objects

class AnonymousUser(object):
    __metaclass__ = ClassExtenderType

    def add_row_perm(self, instance, perm):
        raise NotImplementedError('Anonymous users cannot have any permission.')

    def del_row_perm(self, instance, perm):
        raise NotImplementedError('Anonymous users cannot have any permission.')

    def has_row_perm(self, instance, perm, only_me=False):
        return False

    def get_rows_with_permission(self, instance, perm):
        return []

class Group(object):
    __metaclass__ = ClassExtenderType

    def add_row_perm(self, instance, perm):
        if self.has_row_perm(instance, perm):
            return False
        permission = Permission()
        permission.content_object = instance
        permission.group = self
        permission.name = perm
        permission.save()
        return True
        
    def del_row_perm(self, instance, perm):
        if not self.has_row_perm(instance, perm):
            return False
        content_type = ContentType.objects.get_for_model(instance)
        objects = Permission.objects.filter(user=self, content_type__pk=content_type.id, object_id=instance.id, name=perm)
        objects.delete()
        return True
        
    def has_row_perm(self, instance, perm):
        content_type = ContentType.objects.get_for_model(instance)
        objects = Permission.objects.filter(group=self, content_type__pk=content_type.id, object_id=instance.id, name=perm)
        if objects.count()>0:
            return True
        else:
            return False
            
    def get_rows_with_permission(self, instance, perm):
        content_type = ContentType.objects.get_for_model(instance)
        objects = Permission.objects.filter(group=self, content_type__pk=contet_type.id, name=perm)
        return objects

