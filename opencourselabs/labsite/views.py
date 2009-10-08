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


from collections import defaultdict
from datetime import datetime
import sys
import uuid
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Message
from django.db import IntegrityError, transaction
from django.db.models import Q, Count, Sum
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, RequestContext
from django.template.loader import get_template
from django.utils import simplejson as json
from django.views.generic.list_detail import object_list
from opencourselabs.account.models import Permission
from opencourselabs.assignment.models import Assignment, check_user_submission, check_team_submission
from opencourselabs.bbs.models import Article, Board
from opencourselabs.cloud import CloudException, CloudQueryException
from opencourselabs.cloud.models import Backend, InstanceGroup, Instance, get_api, describe_instances, INSTANCEGROUP_TYPES
from opencourselabs.labsite.decorators import labsite_context, team_context, labsite_perm_required
from opencourselabs.labsite.forms import BrowseForm, CreateTeamForm, ModifyTeamForm, RequestForm, JoinRequestApprovalForm, AddInstancesForm, SettingsForm
from opencourselabs.labsite.models import NewRequest, Labsite, JoinRequest, Team
from opencourselabs.utils import respond_as_json, respond_as_text


def index(request):
    return render_to_response('labsite/index.html', {
    }, context_instance=RequestContext(request))

def browse(request):
    f = BrowseForm(request.GET)
    queries_without_page = request.GET.copy()
    if 'page' in queries_without_page:
        del queries_without_page['page']
    if f.is_valid():
        organization = f.cleaned_data['organization'] # default is u'all'
        course = f.cleaned_data['course']
        status = f.cleaned_data['status']
        if status == u'':
        	status = u'active'
        courses = None
        labsites = Labsite.objects.all()
        if organization != u'all':
            labsites = labsites.filter(organization=organization)
            courses = Labsite.objects.filter(organization=organization).values('course').annotate(Count('course'))
            # TODO: dynamically set the choices of course field to courses.
        elif not course in (u'all', u''):
            # If organization is all, course argument should be inored.
            course = u''
            del queries_without_page['course']
        if not course in (u'all', u''):
            labsites = labsites.filter(course=course)
        if not status in (u'all', u''):
        	labsites = labsites.filter(is_active=(status == u'active'))

        # Repopulate form fields to fill default values which were not specified.
        f = BrowseForm({
        	'organization': organization,
        	'course': course,
        	'status': status,
        })
        labsites = labsites.order_by('-period_begin')
        return object_list(request,
            labsites,
            paginate_by=12,
            template_name='labsite/browse.html',
            template_object_name='labsite',
            extra_context={
                'browse_form': f,
                'course_list': courses,
                'queries': queries_without_page,
            },
        )
    else:
        return HttpResponseBadRequest()

@login_required
def new_request(request):
    err_msg = None
    if request.method == 'POST':
        try:
            f = RequestForm(request.POST)
            new_request = f.save(commit=False)
            new_request.creator = request.user
            new_request.save()
            return render_to_response('labsite/new_request_ok.html', {
            }, context_instance=RequestContext(request))
        except ValueError:
            err_msg = u'Please fill up the form correctly.'
    else:
        f = RequestForm()
    return render_to_response('labsite/new_request.html', {
        'request_form': f,
        'err_msg': err_msg,
    }, context_instance=RequestContext(request))

@labsite_context
@team_context
def dashboard(request, labsite, user_team):
    def check_submitted(assignment):
        if assignment.type == 0:
            return check_user_submission(assignment, request.user)
        else:
            return check_team_submission(assignment, user_team)
    # Show only unsubmitted assignments for the current user.
    assignments = [assignment for assignment in Assignment.objects.filter(belongs_to=labsite) if not check_submitted(assignment)]
    notices = Article.objects.filter(belongs_to=Board.objects.get(belongs_to=labsite, title='default'), is_notice=True)[:3].select_related()
    return render_to_response('labsite/dashboard.html', {
        'labsite': labsite,
        'user_team': user_team,
        'assignment_list': assignments,
        'notice_list': notices,
        'stat': {
            'vm': {
                'allocated': Instance.objects.filter(belongs_to__belongs_to__belongs_to=labsite).count(),
                'total': labsite.num_vm,
            },
            'ip': {
                'allocated': Instance.objects.filter(belongs_to__belongs_to__belongs_to=labsite, elastic_ip__isnull=False).count(),
                'total': labsite.num_ip,
            },
        }
    }, context_instance=RequestContext(request))

@login_required
@labsite_context
@team_context
def new_join_request(request, labsite, user_team):
    if not labsite.is_active:
        return HttpResponseForbidden('This lab is not active.')
    if request.method == 'POST':
        answer1 = request.POST.get('additional_answer1', u'')
        answer2 = request.POST.get('additional_answer2', u'')
        join_request = JoinRequest(owner=request.user, labsite=labsite)
        join_request.additional_answer1 = answer1
        join_request.additional_answer2 = answer2
        join_request.save()

        email_context = Context({
            'host': request.get_host(),
            'requester': join_request.owner,
            'answer1': answer1,
            'answer2': answer2,
            'labsite': labsite,
        })
        title = u'NexR CCI:U - New Join Request to the course lab %(name)s' % {'name': labsite.title}
        text_content = get_template('mail/new_join_request_arrived.txt').render(email_context)
        email = EmailMultiAlternatives(title, text_content, 'no-reply@nexr.co.kr', [
            staff.email for staff in labsite.get_all_staffs()
        ])
        email.send()

        return render_to_response('labsite/join_ok.html', {
            'labsite': labsite,
            'user_team': user_team,
        }, context_instance=RequestContext(request))
    
    return render_to_response('labsite/join.html', {
        'labsite': labsite,
        'user_team': user_team,
    }, context_instance=RequestContext(request))

@login_required
@labsite_perm_required('staff')
@team_context
def list_join_requests(request, labsite, user_team):
    msg = u''.join(request.user.get_and_delete_messages())
    return object_list(request,
        JoinRequest.objects.filter(labsite=labsite),
        template_name='labsite/join_request_list.html',
        template_object_name='join_request',
        extra_context={
            'labsite': labsite,
            'msg': msg,
            'user_team': user_team,
        },
    )

@login_required
@labsite_perm_required('staff')
def approve_join_request(request, labsite):
    f = JoinRequestApprovalForm(request.GET)
    if f.is_valid():
        type = f.cleaned_data['type']
        join_request = get_object_or_404(JoinRequest, id=f.cleaned_data['request_id'])
        join_request.owner.add_row_perm(labsite, type)
        join_request.delete()
        msg = Message()
        msg.user = request.user
        msg.message = u'Ok, %(real_name)s (%(email)s) is now a member of this labsite, as %(type)s.' % {
            'real_name': join_request.owner.get_profile().real_name,
            'email': join_request.owner.email,
            'type': type,
        }
        msg.save()
        email_context = Context({
            'host': request.get_host(),
            'you': join_request.owner,
            'role': type,
            'labsite': labsite,
        })
        title = u'NexR CCI:U - Join request to labsite %(name)s is approved.' % {'name': labsite.title}
        text_content = get_template('mail/join_request_approved.txt').render(email_context)
        email = EmailMultiAlternatives(title, text_content, 'no-reply@nexr.co.kr', [join_request.owner.email])
        email.send()
        return HttpResponseRedirect(reverse('labsite:join-requests', kwargs={'url_key':labsite.url_key}))
    else:
        return HttpResponseBadRequest(u'Bad request.')

@login_required
@labsite_perm_required('staff')
def deny_join_request(request, labsite):
    join_request = get_object_or_404(JoinRequest, id=request.GET.get('request_id'))
    join_request.delete()
    msg = Message()
    msg.user = request.user
    msg.message = u'Ok, %(real_name)s (%(email)s) is denied to join this labsite.' % {
        'real_name': join_request.owner.get_profile().real_name,
        'email': join_request.owner.email,
    }
    msg.save()
    email_context = Context({
        'host': request.get_host(),
        'you': join_request.owner,
        'labsite': labsite,
    })
    title = u'NexR CCI:U - Join request to labsite %(name)s is denied.' % {'name': labsite.title}
    text_content = get_template('mail/join_request_denied.txt').render(email_context)
    email = EmailMultiAlternatives(title, text_content, 'no-reply@nexr.co.kr', [join_request.owner.email])
    email.send()
    return HttpResponseRedirect(reverse('labsite:join-requests', kwargs={'url_key':labsite.url_key}))

@login_required
@labsite_perm_required('staff', 'student')
@team_context
def list_members(request, labsite, user_team):
    msg = u''.join(request.user.get_and_delete_messages())
    return object_list(request,
        labsite.get_all_members().extra(
            select={
                'is_staff': "%s.name='staff'" % Permission._meta.db_table,
                'is_student': "%s.name='student'" % Permission._meta.db_table,
            }
        ),
        template_name='labsite/member_list.html',
        template_object_name='member',
        extra_context={
            'labsite': labsite,
            'msg': msg,
            'user_team': user_team,
        },
    )

@login_required
@labsite_perm_required('staff')
def delete_member(request, labsite):
    target_user = get_object_or_404(User, id=request.GET.get('user'))
    if request.user == target_user:
        return HttpResponseBadRequest(u'You cannot delete yourself.')
    try:
        user_team = Team.objects.get(belongs_to=labsite, members=request.user)
        user_team.members.remove(target_user)
    except Team.DoesNotExist:
        pass
    target_user.del_row_perm(labsite, 'student')
    target_user.del_row_perm(labsite, 'staff')
    msg = Message()
    msg.user = request.user
    msg.message = u'Ok, %(real_name)s (%(email)s) is no longer a member of this labsite.' % {
        'real_name': target_user.get_profile().real_name,
        'email': target_user.email,
    }
    msg.save()
    return HttpResponseRedirect(reverse('labsite:members', kwargs={'url_key':labsite.url_key}))

@login_required
@labsite_perm_required('staff', 'student')
@team_context
def list_teams(request, labsite, user_team):
    msg = u''.join(request.user.get_and_delete_messages())
    return object_list(request,
        Team.objects.filter(belongs_to=labsite).annotate(num_vm_using=Count('instance_group__instance_set')),
        template_name='labsite/team_list.html',
        template_object_name='team',
        extra_context={
            'labsite': labsite,
            'msg': msg,
            'user_team': user_team,
        }
    )

@login_required
@transaction.commit_manually
@labsite_perm_required('staff')
@team_context
def create_team(request, labsite, user_team):
    if not labsite.is_active:
        return HttpResponseForbidden('This lab is not active.')
    err_msg = u''
    if request.method == 'POST':
        f = CreateTeamForm(request.POST)
    else:
        f = CreateTeamForm()

    # Adds dynamic queryset and validation
    f.fields['members'].queryset = labsite.get_all_students()
    f.fields['num_vm'].min_value = 1
    f.fields['num_vm'].max_value = labsite.num_vm - labsite.get_num_allocated_instances()

    if request.method == 'POST':
        if f.is_valid():
            try:
                team = f.save(commit=False)
                team.belongs_to = labsite
                team.save()
                if Team.objects.filter(members__id__in=[member.id for member in f.cleaned_data['members']], belongs_to=team.belongs_to).count() > 0:
                    raise IntegrityError('The user (%s) cannot be members of two or more teams.' % (member.email))
                for member in f.cleaned_data['members']:
                    team.members.add(member)

                backend, is_created = Backend.objects.get_or_create(name=labsite.cloud, credentials=labsite.get_backend_credentials())
                instance_group = InstanceGroup()
                instance_group.backend = backend
                instance_group.belongs_to = team
                instance_group.num_instances = team.num_vm
                instance_group.security_group = backend.get_default_security_group()
                instance_group.keypair_name = 'cciu-t-%s' % uuid.uuid4().hex
                if team.use_hadoop and backend.supports_hadoop_deploy():
                    instance_group.type = INSTANCEGROUP_TYPES.HADOOP_CLUSTER
                else:
                    instance_group.type = INSTANCEGROUP_TYPES.NORMAL

                cloud = backend.get_api()
                fingerprint, material = cloud.create_keypair(instance_group.keypair_name)
                instance_group.private_key = material
                
                instance_group.save()
                instance_group.run()

                msg = Message()
                msg.user = request.user
                msg.message = u'Team "%s" is successfully created.' % team.name
                msg.save()
                transaction.commit()
                return HttpResponseRedirect(reverse('labsite:teams', kwargs={'url_key':labsite.url_key}))
            except CloudQueryException, e:
                print>>sys.stderr, unicode(e)
                err_msg = u'Error: %s' % unicode(e) 
            except (CloudException, IntegrityError), e:
                if isinstance(e, IntegrityError) and len(e.message) == 0:
                    e.message = 'Integrity check failed. Please confirm duplicated fields with other teams.'
                err_msg = u'Error: %s' % e.message
            except Exception, e:
                err_msg = u'Error: %s' % e.message
        else:
            err_msg = u'Please check your input.'
    transaction.rollback()
    return render_to_response('labsite/team_create.html', {
        'labsite': labsite,
        'create_form': f,
        'err_msg': err_msg,
        'user_team': user_team,
    }, context_instance=RequestContext(request))

# TODO: 팀 이름만 수정하는 것은 팀 VM 제어 화면에서 해당 팀의 학생들이 접속한 경우 제목을 클릭하여 AJAX로
#       간단히 고칠 수 있게 하자.

@login_required
@transaction.commit_manually
@labsite_perm_required('staff')
@team_context
def modify_team(request, labsite, user_team):
    if not labsite.is_active:
        return HttpResponseForbidden('This lab is not active.')
    team = get_object_or_404(Team, id=request.GET.get('id'))
    err_msg = u''
    if request.method == 'POST':
        f = ModifyTeamForm(request.POST)
    else:
        f = ModifyTeamForm(initial={
            'name': team.name,
            'members': [member.id for member in team.members.all()]
        })
    f.fields['members'].queryset = labsite.get_all_students()
    f.fields['members'].widget.attrs['size'] = 10
    if request.method == 'POST':
        if f.is_valid():
            try:
                team.name = f.cleaned_data['name']
                team.members = f.cleaned_data['members']
                team.save()
                if Team.objects.filter(
                    ~Q(id=team.id),
                    members__id__in=[member.id for member in f.cleaned_data['members']],
                    belongs_to=team.belongs_to,
                ).count() > 0:
                    raise IntegrityError('The user (%s) cannot be members of two or more teams.' % (member.email))
                for member in f.cleaned_data['members']:
                    team.members.add(member)
                msg = Message()
                msg.user = request.user
                msg.message = u'The team "%s" is modified.' % team.name
                msg.save()
                transaction.commit()
                return HttpResponseRedirect(reverse('labsite:teams', kwargs={'url_key':labsite.url_key}))
            except IntegrityError, e:
                if len(e.message) == 0:
                    e.message = 'Integrity check failed. Please confirm duplicated fields with other teams.'
                err_msg = u'Error: %s' % e.message
        else:
            err_msg = u'Please check your input.'
    transaction.rollback()
    return render_to_response('labsite/team_modify.html', {
        'labsite': labsite,
        'modify_form': f,
        'err_msg': err_msg,
        'user_team': user_team,
    }, context_instance=RequestContext(request))

@login_required
@labsite_perm_required('staff')
@team_context
def delete_team(request, labsite, user_team):
    team = get_object_or_404(Team, id=request.GET.get('id'))
    try:
        instance_group = team.instance_group.get()
        cloud = instance_group.backend.get_api()
        instance_group.terminate()
        cloud.delete_keypair(instance_group.keypair_name)
    except CloudQueryException, e:
        print>>sys.stderr, unicode(e)
    except InstanceGroup.DoesNotExist, e:
        pass
    team.delete()
    msg = Message()
    msg.user = request.user
    msg.message = u'The team "%(name)s" is successfully deleted with its instances.' % {
        'name': team.name,
    }
    msg.save()
    return HttpResponseRedirect(reverse('labsite:teams', kwargs={'url_key':labsite.url_key}))

@login_required
@labsite_perm_required('staff', 'student')
@team_context
def view_team_console(request, labsite, user_team, team_id):
    team = get_object_or_404(Team, id__exact=team_id)
    if not (request.user in User.objects.filter(team=team) or request.user.has_row_perm(labsite, 'staff')):
        raise PermissionDenied('You are not the member of this team.')

    instance_group = InstanceGroup.objects.get(belongs_to=team)
    instances = Instance.objects.filter(belongs_to=instance_group).annotate(is_master=Count('master_group'))
    action = request.GET.get('action', 'view')
    targets = request.GET.getlist('target')
    if len(targets) > 0:
        target_instances = Instance.objects.filter(id__in=targets)
    else:
        target_instances = None
    result = {}

    if action == 'view':
        pass
    elif action == 'reboot':
        cloud = instance_group.backend.get_api()
        if target_instances is None:
            instance_ids = [instance.instance_id for instance in instances]
        else:
            instance_ids = [instance.instance_id for instance in target_instances]
        try:
            result = cloud.reboot_instances(instance_ids)
            return respond_as_json(request, {
                'result': 'success',
                'data': None,
            })
        except CloudQueryException, e:
            print>>sys.stderr, unicode(e)
            return respond_as_json(request, {
                'result': 'failed',
                'errorType': 'Backend',
                'message': e.message,
                'data': e.errors,
            })
    elif action == 'describe':
        cloud = instance_group.backend.get_api()
        if target_instances is None:
            instance_ids = [instance.instance_id for instance in instances]
        else:
            instance_ids = [instance.instance_id for instance in target_instances]
        try:
            if len(instance_ids) == 0:
                result = []
            else:
                result = describe_instances(cloud, instance_ids)
            for item in result:
                if isinstance(item['launch_time'], datetime):
                    item['launch_time'] = item['launch_time'].strftime('%Y-%m-%d %H:%M:%S')
            return respond_as_json(request, {
                'result': 'success',
                'data': result,
            })
        except CloudQueryException, e:
            print>>sys.stderr, unicode(e)
            return respond_as_json(request, {
                'result': 'failed',
                'errorType': 'Backend',
                'message': e.message,
                'data': e.errors,
            })
    elif action == 'getKey':
        if not request.user.has_row_perm(labsite, 'staff') and user_team.hide_private_key:
            return HttpResponseForbidden()
        text = instance_group.private_key
        return respond_as_text(request, text)
    elif action == 'delete':
        if not request.user.has_row_perm(labsite, 'staff'):
            raise PermissionDenied()
        cloud = instance_group.backend.get_api()
        if target_instances is None:
            return respond_as_json(request, {
                'result': 'failed',
                'errorType': 'InputValidation',
                'message': u'You must select one or more instances to delete.',
                'data': None,
            })
        else:
            try:
                result = cloud.terminate_instances([instance.instance_id for instance in target_instances])
            except CloudQueryException, e:
                print>>sys.stderr, unicode(e)
            for instance in target_instances:
                instance.delete()
            return respond_as_json(request, {
                'result': 'success',
                'data': result,
            })
    elif action == 'add':
        if not request.user.has_row_perm(labsite, 'staff'):
            raise PermissionDenied()
        if not labsite.is_active:
            return HttpResponseForbidden('This lab is not active.')
        f = AddInstancesForm(request.POST)
        f.fields['num_instances'].max_value = labsite.num_vm - labsite.get_num_allocated_instances()
        if f.is_valid():
            num_new_instances = f.cleaned_data['num_instances']
            instance_group = InstanceGroup.objects.get(belongs_to=team)
            if f.cleaned_data['redeploy_hadoop']:
                instance_group.type = INSTANCEGROUP_TYPES.HADOOP_CLUSTER
            # existing_instances means the number of instances that are currently registered to the system.
            existing_instances = Instance.objects.filter(belongs_to=instance_group).count()
            instance_group.num_instances = existing_instances
            try:
                instance_group.run(num_new_instances)
            except CloudQueryException, e:
                return respond_as_json(request, {
                    'result': 'failed',
                    'errorType': 'Backend',
                    'message': e.message,
                    'data': e.detail,
                })
            else:
                instance_group.save()
                if team.num_vm < existing_instances + num_new_instances:
                    team.num_vm = existing_instances + num_new_instances
                    team.save()
                return respond_as_json(request, {
                    'result': 'success',
                    'data': None,
                })
        else:
            serializable_errors = dict([(key, [unicode(v) for v in values]) for key, values in f.errors.iteritems()])
            return respond_as_json(request, {
                'result': 'failed',
                'errorType': 'InputValidation',
                'message': u'Check your input.',
                'data': serializable_errors,
            })
    elif action == 'allocateIP':
        if not labsite.is_active:
            return HttpResponseForbidden('This lab is not active.')
        if not request.user.has_row_perm(labsite, 'staff'):
            raise PermissionDenied()
        instance = get_object_or_404(Instance, id=request.GET.get('id'))
        if Instance.objects.filter(belongs_to__belongs_to__belongs_to=labsite, elastic_ip__isnull=False).count() >= labsite.num_ip:
            return respond_as_json(request, {
                'result': 'failed',
                'errorType': 'InputValidation',
                'message': u'You cannot allocate more than %d public IPs for this course lab.' % labsite.num_ip,
                'data': None,
            })
        try:
            ip = instance.allocate_ip()
        except CloudQueryException, e:
            return respond_as_json(request, {
                'result': 'failed',
                'errorType': 'Backend',
                'message': e.message,
                'data': e.detail,
            })
        else:
            return respond_as_json(request, {
                'result': 'success',
                'data': ip,
            })
    elif action == 'releaseIP':
        if not request.user.has_row_perm(labsite, 'staff'):
            raise PermissionDenied()
        instance = get_object_or_404(Instance, id=request.GET.get('id'))
        try:
            instance.release_ip()
        except CloudQueryException, e:
            return respond_as_json(request, {
                'result': 'failed',
                'errorType': 'Backend',
                'message': e.message,
                'data': e.detail,
            })
        else:
            return respond_as_json(request, {
                'result': 'success',
                'data': None,
            })

    return render_to_response('labsite/team_console.html', {
        'labsite': labsite,
        'team': team,
        'user_team': user_team,
        'instance_group': instance_group,
        'instances': instances,
        'add_instances_form': AddInstancesForm(),
    }, context_instance=RequestContext(request))

@login_required
@labsite_perm_required('staff')
@team_context
def view_labsite_console(request, labsite, user_team):
    instances = Instance.objects.filter(belongs_to__belongs_to__belongs_to=labsite).annotate(is_master=Count('master_group')).select_related()
    action = request.GET.get('action', 'view')
    targets = request.GET.getlist('target')
    if len(targets) > 0:
        target_instances = Instance.objects.filter(id__in=targets)
    else:
        target_instances = None
    result = {}

    if action == 'view':
        pass
    elif action == 'reboot':
        cloud = get_api(labsite.cloud, labsite.get_backend_credentials())
        if target_instances is None:
            return respond_as_json(request, {
                'result': 'failed',
                'errorType': 'InputValidation',
                'message': u'You must select instances to reboot.',
                'data': None,
            })
        else:
            instance_ids = [instance.instance_id for instance in target_instances]
        try:
            if len(instance_ids) > 0:
                result = cloud.reboot_instances(instance_ids)
            return respond_as_json(request, {
                'result': 'success',
                'data': None,
            })
        except CloudQueryException, e:
            print>>sys.stderr, unicode(e)
            return respond_as_json(request, {
                'result': 'failed',
                'errorType': 'Backend',
                'message': e.message,
                'data': e.detail,
            })
    elif action == 'describe':
        cloud = get_api(labsite.cloud, labsite.get_backend_credentials())
        if target_instances is None:
            instance_ids = [instance.instance_id for instance in instances]
        else:
            instance_ids = [instance.instance_id for instance in target_instances]
        try:
            if len(instance_ids) == 0:
                result = []
            else:
                result = describe_instances(cloud, instance_ids)
        except CloudQueryException, e:
            print>>sys.stderr, unicode(e)
            return respond_as_json(request, {
                'result': 'failed',
                'errorType': 'Backend',
                'message': e.message,
                'data': e.detail,
            })
        else:
            for item in result:
                if isinstance(item['launch_time'], datetime):
                    item['launch_time'] = item['launch_time'].strftime('%Y-%m-%d %H:%M:%S')
            return respond_as_json(request, {
                'result': 'success',
                'data': result,
            })
    elif action == 'allocateIP':
        if not labsite.is_active:
            return HttpResponseForbidden('This lab is not active.')
        if not request.user.has_row_perm(labsite, 'staff'):
            raise PermissionDenied()
        instance = get_object_or_404(Instance, id=request.GET.get('id'))
        if Instance.objects.filter(belongs_to__belongs_to__belongs_to=labsite, elastic_ip__isnull=False).count() >= labsite.num_ip:
            return respond_as_json(request, {
                'result': 'failed',
                'errorType': 'InputValidation',
                'message': u'You cannot allocate more than %d public IPs for this course lab.' % labsite.num_ip,
                'data': None,
            })
        try:
            ip = instance.allocate_ip()
        except CloudQueryException, e:
            return respond_as_json(request, {
                'result': 'failed',
                'errorType': 'Backend',
                'message': e.message,
                'data': e.detail,
            })
        else:
            return respond_as_json(request, {
                'result': 'success',
                'data': ip,
            })
    elif action == 'releaseIP':
        instance = get_object_or_404(Instance, id=request.GET.get('id'))
        if not request.user.has_row_perm(labsite, 'staff'):
            raise PermissionDenied()
        try:
            instance.release_ip()
        except CloudQueryException, e:
            return respond_as_json(request, {
                'result': 'failed',
                'errorType': 'Backend',
                'message': e.message,
                'data': e.detail,
            })
        else:
            return respond_as_json(request, {
                'result': 'success',
                'data': None,
            })

    queries_without_page = request.GET.copy()
    if 'page' in queries_without_page:
        del queries_without_page['page']
    current_team = int(request.GET.get('team', '-1'))
    if current_team != -1:
        instances = instances.filter(belongs_to__belongs_to=Team.objects.get(id=current_team))
    teams = Team.objects.filter(belongs_to=labsite)
    return object_list(request,
        instances,
        paginate_by=12,
        template_name='labsite/labsite_console.html',
        template_object_name='instance',
        extra_context = {
            'labsite': labsite,
            'user_team': user_team,
            'teams': teams,
            'current_team': current_team,
            'queries': queries_without_page,
        },
    )

@login_required
@labsite_perm_required('staff')
@team_context
def modify_settings(request, labsite, user_team):
    if not labsite.is_active:
        return HttpResponseForbidden('This lab is not active.')
    err_msg = u''
    msg = u''
    if request.method == 'POST':
        f = SettingsForm(request.POST)
        if f.is_valid():
            labsite.title = f.cleaned_data['title']
            labsite.additional_question1 = f.cleaned_data['question1']
            labsite.additional_question2 = f.cleaned_data['question2']
            labsite.description = f.cleaned_data['description']
            labsite.save()
            msg = u'Settings are saved.'
        else:
            err_msg = u'Please fill up the fields correctly.'
    else:
        f = SettingsForm(initial={
            'title': labsite.title,
            'question1': labsite.additional_question1,
            'question2': labsite.additional_question2,
            'description': labsite.description,
        })
    return render_to_response('labsite/settings.html', {
        'labsite': labsite,
        'user_team': user_team,
        'settings_form': f,
        'err_msg': err_msg,
        'msg': msg,
    }, context_instance=RequestContext(request))
