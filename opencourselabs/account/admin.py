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
Account model-admins for ACCI.
"""

from django.contrib import admin
from django.contrib.auth.models import User
from .models import UserProfile, RegisterRequest, Permission

class PermissionAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'content_object', 'user', 'group', 'name')
    list_filter = ('name',)
    search_fields = ['object_id', 'content_type', 'user', 'group']
    raw_id_fields = ['user', 'group']

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'real_name', 'organization')

class RegisterRequestAdmin(admin.ModelAdmin):
    list_display = ('key', 'real_name', 'email', 'organization', 'created_at')
    ordering = ('organization',)

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'real_name', 'organization', 'is_staff')
    ordering = ('-is_staff', 'email', )
    exclude = ('first_name', 'last_name', 'user_permissions')

    def real_name(self, obj):
        return obj.get_profile().real_name

    def organization(self, obj):
        return obj.get_profile().get_organization_display()


admin.site.unregister(User)     # overrides Django's default UserAdmin
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Permission, PermissionAdmin)
admin.site.register(RegisterRequest, RegisterRequestAdmin)
