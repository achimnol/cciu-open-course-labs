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


from datetime import datetime
from django.contrib import admin
from django.contrib.admin import helpers
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render_to_response
from django.template import RequestContext, Context
from django.template.loader import get_template
from opencourselabs.bbs.models import Board, Article, Tag
from .models import NewRequest, Labsite, Team, JoinRequest, REQUEST_STATUS

class NewRequestAdmin(admin.ModelAdmin):
    list_display = ('creator', 'title', 'course', 'organization', 'cloud', 'num_vm', 'num_ip', 'period_begin', 'period_end', 'contact_cellphone', 'status', 'created_at', 'approved_at')
    list_display_links = ('title',)
    list_filter = ('status', 'organization')
    list_per_page = 50
    ordering = ('-created_at', 'organization')
    actions = ['deny_request', 'approve_request']

    def approve_request(self, request, queryset):
        if request.user.is_superuser == False:
            raise PermissionDenied()
        if queryset.count() != 1:
            self.message_user(request, u'You should choose only one request to approve.')
            return None

        request_object = queryset.get()
        if request_object.status != REQUEST_STATUS.UNREVIEWED:
            self.message_user(request, u'This request has been approved/denied already.')
            return None

        # Avoid a circular import.
        from opencourselabs.labsite.forms import RequestApprovalForm

        # If the user has confirmed approval, do the actual process needed.
        if request.POST.get('post'):
            approval_form = RequestApprovalForm(request.POST)
            if approval_form.is_valid():
                num_vm = approval_form.cleaned_data['num_vm']
                num_ip = approval_form.cleaned_data['num_ip']
                # TODO: check num_vm once again.

                # Change status.
                request_object.status = REQUEST_STATUS.APPROVED
                request_object.num_vm = num_vm
                request_object.num_ip = num_ip
                request_object.approved_at = datetime.now()
                request_object.save()

                # Create the labsite.
                labsite = Labsite()
                labsite.owner = request_object.creator
                labsite.title = request_object.title
                labsite.course = request_object.course
                labsite.description = request_object.description
                labsite.organization = request_object.organization
                labsite.cloud = request_object.cloud
                # External services require explicit authentication info.
                if request_object.cloud != u'nexr-vc3':
                    labsite.access_key = request_object.access_key
                    labsite.secret_key = request_object.secret_key
                labsite.num_vm = request_object.num_vm
                labsite.num_ip = request_object.num_ip
                labsite.additional_question1 = request_object.additional_question1
                labsite.additional_question2 = request_object.additional_question2
                labsite.period_begin = request_object.period_begin
                labsite.period_end = request_object.period_end
                labsite.contact_cellphone = request_object.contact_cellphone
                labsite.contact_alternative = request_object.contact_alternative
                labsite.is_active = False   # NOTE: inactive at first, so sysop should enable it.
                labsite.save()
                labsite.owner.add_row_perm(labsite, 'staff')

                # Create a board for the labsite.
                board = Board()
                board.belongs_to = labsite
                board.owner = request_object.creator
                board.title = u'default'
                board.save()

                # Send notification mail.
                mail_context = RequestContext(request, {
                    'labsite': labsite,
                    'request': request_object,
                    'you': labsite.owner,
                    'host': request.get_host(),
                })
                text_content = get_template('mail/labsite_new_request_approved.txt').render(mail_context)
                msg = EmailMultiAlternatives(u'NexR CCI:U Labsite Request Approved', text_content,
                    'no-reply@nexr.co.kr', [labsite.owner.email])
                msg.send()

                self.message_user(request, u'The request "%s" has been approved, and a notifiation mail has been sent to %s' % (request_object, request.user.email))
            else:
                self.message_user(request, u'Invalid parameters.')
            return None

        approval_form = RequestApprovalForm(initial={
            'num_vm': request_object.num_vm,
            'num_ip': request_object.num_ip,
        })
        return render_to_response('labsite/admin/approve_new_request_confirmation.html', {
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'request': request_object,
            'approval_form': approval_form,
        }, context_instance=RequestContext(request))
    approve_request.short_description = u'Approve the selected request'

    def deny_request(self, request, queryset):
        if request.user.is_superuser == False:
            raise PermissionDenied()

        if queryset.count() != 1:
            self.message_user(request, u'You should choose only one request to deny.')
            return None

        request_object = queryset.get()
        if request_object.status != REQUEST_STATUS.UNREVIEWED:
            self.message_user(request, u'This request has been approved/denied already.')
            return None

        if request.POST.get('post'):

            # Change status.
            request_object.status = REQUEST_STATUS.DENIED
            request_object.approved_at = datetime.now()
            request_object.save()

            # Send notification mail.
            mail_context = RequestContext(request, {
                'request': request_object,
                'you': request_object.creator,
                'host': request.get_host(),
            })
            text_content = get_template('mail/labsite_new_request_denied.txt').render(mail_context)
            msg = EmailMultiAlternatives(u'NexR CCI:U Labsite Request Denied', text_content,
                'no-reply@nexr.co.kr', [request_object.creator.email])
            msg.send()
                
            self.message_user(request, u'The request "%s" has been denied, and a notification mail has been sent to %s' % (request_object, request.user.email))
            return None

        return render_to_response('labsite/admin/deny_new_request_confirmation.html', {
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'request': request_object,
        }, context_instance=RequestContext(request))
    deny_request.short_description = u'Deny selected requests'

class LabsiteAdmin(admin.ModelAdmin):
    exclude = ('url_key',)
    list_display = ('url_key', 'title', 'course', 'organization', 'cloud', 'num_vm', 'num_ip', 'period_begin', 'period_end', 'contact_cellphone', 'is_active', 'created_at')
    list_display_links = ('url_key', 'title')
    list_filter = ('is_active', 'organization')
    ordering = ('-created_at', 'organization')

class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'belongs_to', 'num_vm')
    ordering = ('name',)

class JoinRequestAdmin(admin.ModelAdmin):
    list_display = ('owner', 'labsite', 'additional_answer1', 'additional_answer2', 'created_at')


admin.site.register(Labsite, LabsiteAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(NewRequest, NewRequestAdmin)
admin.site.register(JoinRequest, JoinRequestAdmin)

