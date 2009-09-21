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


import random
from django.contrib import auth
from django.contrib.auth.models import User, get_hexdigest
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import Context, RequestContext
from django.template.loader import get_template
from opencourselabs.account.models import UserProfile, RegisterRequest
from opencourselabs.account.forms import LoginForm, CreateForm
from opencourselabs.labsite.models import Labsite, Team

def create(request):
    err_msg = u''
    if request.method == 'POST':
        create_form = CreateForm(request.POST)
        if create_form.is_valid():

            real_name = create_form.cleaned_data['real_name']
            email = create_form.cleaned_data['email']
            organization = create_form.cleaned_data['organization']
            password = create_form.cleaned_data['password']

            try:
                # Check uniqueness of email (real_name may be duplicated.)
                existing_user = User.objects.filter(email__exact=email).count()
                if existing_user > 0:
                    raise IntegrityError()

                # Generate a random key for this registration request.
                available_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
                key = ''.join([random.choice(available_chars) for i in xrange(32)])

                # Make a salt for password generation.
                algo = 'sha1'
                salt = ''.join([random.choice(available_chars) for i in xrange(5)])

                # Create a pending request record.
                record = RegisterRequest()
                record.key = key
                record.real_name = real_name
                record.email = email
                record.organization = organization
                record.password = '%s$%s$%s' % (algo, salt, get_hexdigest(algo, salt, password))
                record.save()

                # Send a verification email.
                mail_context = Context({
                    'host': request.get_host(),
                    'key': key,
                })
                text_content = get_template('mail/account_verification.txt').render(mail_context)
                html_content = get_template('mail/account_verification.html').render(mail_context)
                msg = EmailMultiAlternatives(u'NexR CCI:U Account Verification', text_content,
                    'no-reply@nexr.co.kr', [email])
                msg.attach_alternative(html_content, 'text/html')
                msg.send()
                
                return render_to_response('account/create_ok.html', {
                    'err_msg': err_msg,
                }, context_instance=RequestContext(request))
            except IntegrityError:
                err_msg = u'The email you have entered is already being used.'
            except Exception, e:
               err_msg = u'Sorry, we could not send the verfication email. (%s)' % e.message
        else:
            err_msg = u'You have to fill the required fields with valid input.'
    else:
        create_form = CreateForm()

    return render_to_response('account/create.html', {
        'create_form': create_form,
        'err_msg': err_msg,
    }, context_instance=RequestContext(request))

def verify_email(request):
    # Check the validity.
    try:
        record = RegisterRequest.objects.get(key=request.GET['key'])
    except RegisterRequest.DoesNotExist:
        return HttpResponseNotFound()
    except:
        return HttpResponseBadRequest()

    # Create the actual user.
    user = User()
    user.username = record.email
    user.email = record.email
    user.password = record.password
    user.is_active = True
    user.is_staff = False
    user.is_superuser = False
    user.save()
    profile = UserProfile()
    profile.user = user
    profile.real_name = record.real_name
    profile.organization = record.organization
    profile.save()
    record.delete()

    return render_to_response('account/verify_email.html', {
        'success': True,
    }, context_instance=RequestContext(request))

def login(request):
    next_url = request.GET.get('next', '/')
    err_msg = u''
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():

            user = auth.authenticate(username=login_form.cleaned_data['email'], password=login_form.cleaned_data['password'])
            if user is None:
                # Login failed.
                err_msg = u'Invalid username or password.'
            else:
                # Login OK
                auth.login(request, user)
                return HttpResponseRedirect(next_url)

        else:
            err_msg = u'You have to fill the required fields.'
    else:
        login_form = LoginForm()

    response = render_to_response('account/login.html', {
        'login_form': login_form,
        'next_url': next_url,
        'err_msg': err_msg,
    }, context_instance=RequestContext(request))
    response['X-Reason-For-Redirect'] = 'login'
    return response

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/')

@login_required
def my_page(request):
    # Teams and labsites that the user belongs to.
    teams = Team.objects.filter(members=request.user).select_related()
    # Labsites that the user belongs to, but where user is not in any team.
    labsites = [perm.content_object for perm in request.user.get_rows_with_permission(
        Labsite, ['staff', 'student']
    ) if not perm.content_object.id in [team.belongs_to.id for team in teams]]
    return render_to_response('account/mypage.html', {
        'teams': teams,
        'labsites': labsites,
    }, context_instance=RequestContext(request))
