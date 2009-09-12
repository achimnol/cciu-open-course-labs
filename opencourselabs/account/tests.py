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


from __future__ import with_statement   # for Python 2.5
import sys
import re
from StringIO import StringIO
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.core import mail
from opencourselabs.testutils import StdoutCollector
from opencourselabs.testutils.minimock import Mock
from opencourselabs.account.models import UserProfile, RegisterRequest

class AccountViewTest(TestCase):

    def test_create(self):
        """
        Tests the process of creating user including registration request
        and email verification.
        """

        client = Client()
        response = client.post('/account/create/', {
            'real_name': u'testuser',
            'email': u'test@example.com',
            'organization': u'kaist',
            'password': u'1234',
        })
        self.failUnlessEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/create_ok.html')
        self.assertEqual(response.context['err_msg'], u'')
        self.assertEqual(RegisterRequest.objects.count(), 1)

        # Check for a duplicated request.
        response = client.post('/account/create/', {
            'real_name': u'testuser',
            'email': u'test@example.com',
            'organization': u'kaist',
            'password': u'1234',
        })
        self.failUnlessEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/create.html')
        self.failIfEqual(response.context['err_msg'], u'', 'This message should be shown: "%s"' % response.context['err_msg'])
        self.assertEqual(RegisterRequest.objects.count(), 1)

        # Check email.
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, u'NexR CCI:U Account Verification')
        matches = re.search(ur'key=([0-9a-zA-Z]{32})', mail.outbox[0].body)
        self.failIf(matches is None, 'Email should contain a request key.')
        key = matches.group(1)

        try:
            record = RegisterRequest.objects.get(real_name='testuser')
        except RegisterRequest.DoesNotExist:
            self.fail('The corresponding RegisterRequest object does not exist. (with username)')
        try:
            record = RegisterRequest.objects.get(key=key)
        except RegisterRequest.DoesNotExist:
            self.fail('The corresponding RegisterRequest object does not exist. (with key)')

        # Check with an invalid key.
        response = client.get('/account/verify/', {'key': 'XXXXXXX'})
        self.failUnlessEqual(response.status_code, 404)
        self.assertEqual(RegisterRequest.objects.count(), 1)

        # Now check the behaviour with the verification key.
        response = client.get('/account/verify/', {'key': key})
        self.failUnlessEqual(response.status_code, 200)
        self.assertTrue(response.context['success'])
        self.assertEqual(RegisterRequest.objects.count(), 0)

        try:
            user = User.objects.get(username=u'test@example.com')
            self.assertTrue(user.is_active)
            self.assertFalse(user.is_superuser)
            self.assertFalse(user.is_staff)
            self.assertEqual(user.email, u'test@example.com')
            self.assertEqual(user.userprofile.organization, u'kaist')
            self.assertTrue(user.check_password(u'1234'), 'The password saved is "%s"' % user.password)
        except User.DoesNotExist:
            self.fail('The \'testuser\' user was not created.')

        # Here, a valid new user has been added.

        # Check for a duplicated user.
        response = client.post('/account/create/', {
            'real_name': u'testuser',
            'email': u'test@example.com',
            'organization': u'kaist',
            'password': u'1234',
        })
        self.failUnlessEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/create.html')
        self.failIfEqual(response.context['err_msg'], u'')
        self.assertEqual(RegisterRequest.objects.count(), 0)

        # Destroy the created user to avoid conflicts with Django's unit-tests.
        user.get_profile().delete()
        user.delete()
