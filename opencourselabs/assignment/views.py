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
import shutil
import os
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Message, User
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseServerError, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from opencourselabs.labsite.decorators import labsite_context, team_context, labsite_perm_required
from opencourselabs.labsite.models import Labsite, Team
from opencourselabs.repository.models import File, Directory, get_or_create_directory, delete_file, DIRECTORY_TYPES
from opencourselabs.utils import respond_as_attachment
from .models import ASSIGNMENT_TYPES
from .models import Assignment, Submission
from .models import check_user_submission, check_team_submission
from .forms import CreateForm, ModifyForm, SubmitForm, MetadataForm, ResubmitForm

@login_required
@labsite_perm_required('staff')
@team_context
def create(request, labsite, user_team):
    if not labsite.is_active:
        return HttpResponseForbidden('This lab is not active.')
    err_msg = u''
    if request.method == 'POST':
        f = CreateForm(request.POST)
        if f.is_valid():
            assignment = Assignment()
            assignment.belongs_to = labsite
            assignment.due_date = datetime.combine(f.cleaned_data['due_date'], f.cleaned_data['due_time'])
            assignment.name = f.cleaned_data['name']
            assignment.type = f.cleaned_data['type']
            assignment.description = f.cleaned_data['description']
            dir = get_or_create_directory(
                labsite.url_key, u'%s' % assignment.id,
                DIRECTORY_TYPES.PRIVATE,
                u'Submission box for assignment'
            )
            assignment.repos_dir = dir
            assignment.save()
            for temp_file in f.cleaned_data['attachments']:
                file = dir.file_set.create(
                    name=temp_file.original_name,
                    owner=request.user,
                    team=user_team if assignment.type == ASSIGNMENT_TYPES.TEAM else None,
                    description = f.cleaned_data['description'],
                    size = os.stat(temp_file.saved_path).st_size,
                )
                assignment.attachments.add(file)
                shutil.move(temp_file.saved_path, file.get_real_path())
                temp_file.delete()
            msg = Message()
            msg.user = request.user
            msg.message = u'New assignment "%s" is created.' % assignment.name
            msg.save()
            return HttpResponseRedirect(reverse('labsite:assignment-list', kwargs={'url_key': labsite.url_key}))
        else:
            err_msg = u'Please fill up the form correctly.'
    else:
        f = CreateForm()
    return render_to_response('assignment/create.html', {
        'labsite': labsite,
        'user_team': user_team,
        'create_form': f,
        'err_msg': err_msg,
    }, context_instance=RequestContext(request))

@login_required
@labsite_perm_required('staff')
@team_context
def modify(request, labsite, user_team):
    err_msg = u''
    assignment = get_object_or_404(Assignment, id=request.GET.get('id'))
    if request.method == 'POST':
        f = ModifyForm(request.POST)
        if f.is_valid():
            assignment.due_date = datetime.combine(f.cleaned_data['due_date'], f.cleaned_data['due_time'])
            assignment.name = f.cleaned_data['name']
            assignment.description = f.cleaned_data['description']
            assignment.save()
            dir = get_or_create_directory(labsite.url_key, u'%s' % assignment.id, 1, u'Submission box for assignment')
            if f.cleaned_data['remove_attachments']:
                for file in assignment.attachments.all():
                    delete_file(file)
            for temp_file in f.cleaned_data['attachments']:
                file = dir.file_set.create(
                    name=temp_file.original_name,
                    owner=request.user,
                    team=user_team if assignment.type == ASSIGNMENT_TYPES.TEAM else None,
                    description = f.cleaned_data['description'],
                    size = os.stat(temp_file.saved_path).st_size,
                )
                assignment.attachments.add(file)
                shutil.move(temp_file.saved_path, file.get_real_path())
                temp_file.delete()
            msg = Message()
            msg.user = request.user
            msg.message = u'The assignment "%s" is modified.' % assignment.name
            msg.save()
            return HttpResponseRedirect(reverse('labsite:assignment-list', kwargs={'url_key': labsite.url_key}))
        else:
            err_msg = u'Please fill up the form correctly.'
    else:
        f = ModifyForm(initial={
            'name': assignment.name,
            'description': assignment.description,
            'due_date': assignment.due_date.date(),
            'due_time': assignment.due_date.time(),
        })
    return render_to_response('assignment/modify.html', {
        'labsite': labsite,
        'user_team': user_team,
        'assignment': assignment,
        'modify_form': f,
        'err_msg': err_msg,
    }, context_instance=RequestContext(request))

@login_required
@labsite_perm_required('staff', 'student')
@team_context
def detail(request, labsite, user_team):
    assignment = get_object_or_404(Assignment, id=request.GET.get('id'))
    submissions = Submission.objects.filter(belongs_to=assignment)
    try:
        if assignment.type == ASSIGNMENT_TYPES.INDIVIDUAL:
            submission = Submission.objects.get(belongs_to=assignment, submitter=request.user)
        else:
            submission = Submission.objects.get(belongs_to=assignment, team=user_team)
        did_submit = True
    except Submission.DoesNotExist:
        submission = None
        did_submit = False

    return render_to_response('assignment/detail.html', {
        'labsite': labsite,
        'user_team': user_team,
        'assignment': assignment,
        'submission_list': submissions,
        'did_submit': did_submit,
        'submission': submission,
    }, context_instance=RequestContext(request))

@login_required
@labsite_perm_required('staff', 'student')
@team_context
def download(request, labsite, user_team):
    assignment = get_object_or_404(Assignment, id=request.GET.get('assignment_id'))
    file = get_object_or_404(File, id=request.GET.get('file_id'))
    return respond_as_attachment(request, file.get_real_path(), file.name)

@login_required
@labsite_perm_required('staff', 'student')
@team_context
def list(request, labsite, user_team):
    assignments = Assignment.objects.filter(belongs_to=labsite).annotate(
        team_submission_count=Count('submission_set__team')
    ).annotate(
        user_submission_count=Count('submission_set__submitter')
    ).order_by('due_date')
    msg = u''.join(request.user.get_and_delete_messages())
    return render_to_response('assignment/list.html', {
        'labsite': labsite,
        'user_team': user_team,
        'msg': msg,
        'assignment_list': assignments,
        'total_users': User.objects.filter(
            row_permission_set__name='student', # Staffs don't have to submit. :P
            row_permission_set__object_id=labsite.id
        ).count(),
        'total_teams': Team.objects.filter(belongs_to=labsite).count(),
    }, context_instance=RequestContext(request))

@login_required
@transaction.commit_manually
@labsite_perm_required('student', 'staff')
@team_context
def submit(request, labsite, user_team):
    if not labsite.is_active:
        return HttpResponseForbidden('This lab is not active.')
    warn_msg = err_msg = u''
    assignment = get_object_or_404(Assignment, id=request.GET.get('id'))
    submission = None
    if user_team is None and assignment.type == ASSIGNMENT_TYPES.TEAM:
        err_msg = u'To submit a team assignment, you should be a member of a team.'

    # This view also handles re-submissions.
    if assignment.type == ASSIGNMENT_TYPES.INDIVIDUAL:
        did_submit = check_user_submission(assignment, request.user)
    else:
        did_submit = check_team_submission(assignment, user_team)
    if did_submit:
        TheForm = ResubmitForm
    else:
        TheForm = SubmitForm

    if request.method == 'POST':
        f = TheForm(request.POST)
        meta_f = MetadataForm(request.POST)
        if f.is_valid():

            if isinstance(f, ResubmitForm):
                if assignment.type == ASSIGNMENT_TYPES.INDIVIDUAL:
                    submission = assignment.submission_set.get(submitter=request.user)
                else:
                    submission = assignment.submission_set.get(team=user_team)
                    submission.submitter = request.user
                submission.description = f.cleaned_data['description']
                submission.submitted = datetime.now()
                submission.save()
            else:
                submission = assignment.submission_set.create(
                    description=f.cleaned_data['description'],
                    submitter=request.user,
                    team=user_team if assignment.type == ASSIGNMENT_TYPES.TEAM else None,
                )
            temp_files = f.cleaned_data['attachments']
            if user_team is None:
                dir_id = 0
            else:
                dir_id = user_team.id
            try:
                dir = get_or_create_directory(labsite.url_key, u'%s/%s' % (assignment.id, dir_id), 1, u'Box for Team')
                if isinstance(f, ResubmitForm) and f.cleaned_data['remove_attachments']:
                    for file in submission.attachments.all():
                        delete_file(file)
                for temp_file in temp_files:
                    file = dir.file_set.create(
                        name=temp_file.original_name,
                        owner=request.user,
                        team=user_team if assignment.type == ASSIGNMENT_TYPES.TEAM else None,
                        description = f.cleaned_data['description'],
                        size = os.stat(temp_file.saved_path).st_size,
                        # TODO: add appropriate metadata
                        metadata = {},
                    )
                    submission.attachments.add(file)

                    # NOTE: If /tmp and storage lies in different filesystems,
                    #       this will perform copy and remove subsequently.
                    shutil.move(temp_file.saved_path, file.get_real_path())
                    temp_file.delete()

                msg = Message()
                msg.user = request.user
                if isinstance(f, ResubmitForm):
                    msg.message = u'Submission to "%s" is modified successfully.' % assignment.name
                else:
                    msg.message = u'Submission to "%s" is done successfully.' % assignment.name
                msg.save()
                transaction.commit()
                return HttpResponseRedirect(reverse('labsite:assignment-list', kwargs={'url_key': labsite.url_key}))
            except OSError, e:
                err_msg = u'Error: %s' % u', '.join(e.args)

        else:
            err_msg = u'Please fill up the form correctly.'
    else:
        if did_submit:
            warn_msg = u'You are resubmitting the assignment!'
            if assignment.type == ASSIGNMENT_TYPES.INDIVIDUAL:
                submission = assignment.submission_set.get(submitter=request.user)
            else:
                submission = assignment.submission_set.get(team=user_team)
            if assignment.type == ASSIGNMENT_TYPES.TEAM and submission.submitter is not request.user:
                warn_msg += u'\n(Your team has submitted already.)'
            f = TheForm({'description': submission.description})
            # TODO: implement metadata handling
            meta_f = MetadataForm()
        else:
            f = TheForm()
            meta_f = MetadataForm()
    transaction.rollback()
    return render_to_response('assignment/submit.html', {
        'labsite': labsite,
        'user_team': user_team,
        'submit_form': f,
        'metadata_form': meta_f,
        'assignment': assignment,
        'submission': submission,
        'err_msg': err_msg,
        'warn_msg': warn_msg,
    }, context_instance=RequestContext(request))

@login_required
@labsite_perm_required('staff', 'student')
@team_context
def submission_download(request, labsite, user_team):
    submission = get_object_or_404(Submission, id=request.GET.get('submission_id'))
    file = get_object_or_404(File, id=request.GET.get('file_id'))
    if not os.path.isfile(file.get_real_path()):
        raise HttpResponseServerError('Cannot locate the actual file.')

    # Normal students should not be able to access other's submissions.
    if not request.user.has_row_perm(labsite, 'staff'):
        if submission.belongs_to.type == ASSIGNMENT_TYPES.INDIVIDUAL and submission.submitter != request.user:
            raise PermissionDenied()
        if submission.belongs_to.type == ASSIGNMENT_TYPES.TEAM and submission.team != user_team:
            raise PermissionDenied()

    return respond_as_attachment(request, file.get_real_path(), file.name)

@login_required
@labsite_perm_required('staff', 'student')
@team_context
def submission_detail(request, labsite, user_team):
    submission = get_object_or_404(Submission, id=request.GET.get('id'))

    # Normal students should not be able to access other's submissions.
    if not request.user.has_row_perm(labsite, 'staff'):
        if submission.belongs_to.type == ASSIGNMENT_TYPES.INDIVIDUAL and submission.submitter != request.user:
            raise PermissionDenied()
        if submission.belongs_to.type == ASSIGNMENT_TYPES.TEAM and submission.team != user_team:
            raise PermissionDenied()

    return render_to_response('assignment/submission_detail.html', {
        'labsite': labsite,
        'user_team': user_team,
        'assignment': submission.belongs_to,
        'submission': submission,
    }, context_instance=RequestContext(request))
