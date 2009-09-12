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


from datetime import date
from django.conf import settings
from django.contrib.admin import helpers
from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from opencourselabs.labsite.decorators import labsite_context, team_context, labsite_perm_required
from opencourselabs.labsite.models import NewRequest, Labsite, JoinRequest, Team, REQUEST_STATUS
from opencourselabs.labsite.admin import NewRequestAdmin
from opencourselabs.labsite.views import labsite_context, labsite_perm_required

class AnonymousViewTest(TestCase):
    fixtures = ['test-users.json']

    def test_new_request(self):
        """
        Tests whether new labsite request is processed properly.

        Note that there is no limit for adding duplicated items
        because it is hard to define differences between two requests.
        """

        # TODO: Should we impose restrictions such that one user can make only
        #       one request per day?

        self.client.login(username='test-user@nexr.co.kr', password='1234')
        response = self.client.post('/lab/request/new/', {
            'title': u'Test Labsite',
            'course': u'CS101',
            'description': u'blah blah blah',
            'organization': u'kaist',
            'cloud': 'nexr-vc3',
            'num_vm': 100,
            'num_ip': 10,
            'period_begin': u'2009-06-01',
            'period_end': u'2009-08-31',
            'additional_question1': u'asdf',
            'contact_cellphone': u'010-1234-5678',
        })
        self.failUnlessEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'labsite/new_request_ok.html')
        self.assertEqual(NewRequest.objects.count(), 1)
        self.client.logout()

class LabsiteViewTest(TestCase):
    fixtures = ['test-users.json', 'test-labsite-models.json']

    def setUp(self):
        settings.TESTING = True
        labsite = Labsite.objects.get(id=1)
        User.objects.get(id=10).add_row_perm(labsite, 'staff')
        User.objects.get(id=11).add_row_perm(labsite, 'student')
        self.client.login(username='test-user@nexr.co.kr', password='1234')

    def tearDown(self):
        self.client.logout()
        settings.TESTING = False

    def test_approve_join_request(self):
        pass

    def test_delete_team(self):
        pass

    def test_delete_member(self):
        labsite = Labsite.objects.get(id=1)
        team = Team()
        team.name = u'TestTeam'
        team.num_vm = 5
        team.belongs_to = labsite
        team.save()
        user10 = User.objects.get(id=10)
        user11 = User.objects.get(id=11)
        user10.add_row_perm(labsite, 'staff')
        user11.add_row_perm(labsite, 'student')
        team.members.add(user10)
        team.members.add(user11)
        # Try to delete a non-existent user.
        response = self.client.get('/lab/kaist-abcdef/manage/members/delete/?user=999', follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(team.members.all().count(), 2)
        # Try to delete a student.
        response = self.client.get('/lab/kaist-abcdef/manage/members/delete/?user=11', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(team.members.all().count(), 1)
        # Try to delete myself.
        response = self.client.get('/lab/kaist-abcdef/manage/members/delete/?user=10', follow=True)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(team.members.all().count(), 1)
        self.assertTrue(user10.has_row_perm(labsite, 'staff'))
        self.assertFalse(user11.has_row_perm(labsite, 'student'))

class LabsiteViewWithTransactionsTest(TransactionTestCase):
    fixtures = ['test-users.json', 'test-labsite-models.json']

    def setUp(self):
        settings.TESTING = True  # To prevent creating real API.
        labsite = Labsite.objects.get(id=1)
        User.objects.get(id=10).add_row_perm(labsite, 'staff')
        User.objects.get(id=11).add_row_perm(labsite, 'student')
        self.client.login(username='test-user@nexr.co.kr', password='1234')

    def tearDown(self):
        self.client.logout()
        settings.TESTING = False

    def test_create_team(self):
        labsite = Labsite.objects.get(id=1)
        self.assertTrue(11 in [student.id for student in labsite.get_all_students()])
        response = self.client.post('/lab/kaist-abcdef/manage/teams/create/', {
            'members': (11,),
            'num_vm': labsite.num_vm + 1,
            'name': u'TestTeam',
            'belongs_to': labsite.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'create_form', 'num_vm', u'Ensure this value is less than or equal to %d.' % labsite.num_vm)
        self.assertEqual(Team.objects.count(), 0)

        response = self.client.post('/lab/kaist-abcdef/manage/teams/create/', {
            'members': (11,),
            'num_vm': labsite.num_vm - 1,
            'name': u'TestTeam',
            'belongs_to': labsite.id,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, u'Team &quot;TestTeam&quot; is successfully created.')
        self.assertEqual(Team.objects.count(), 1)

        response = self.client.post('/lab/kaist-abcdef/manage/teams/create/', {
            'members': (11,),
            'num_vm': 1,
            'name': u'TestTeam2',
            'belongs_to': labsite.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cannot be members of two or more teams.')
        self.assertEqual(Team.objects.count(), 1)


class ViewHelperTest(TestCase):
    fixtures = ['test-users.json', 'test-labsite-models.json']

    def test_labsite_context_decorator(self):

        @labsite_context
        def my_view(request, labsite):
            return labsite

        class Dummy(object):
            pass

        request = Dummy()
        request.user = User.objects.get(id=10)
        labsite = my_view(request, 'kaist-abcdef')
        self.assertEqual(labsite.url_key, 'kaist-abcdef')
        self.assertRaises(Http404, lambda: my_view(request, 'kaist-xxxxxx'))

    def test_labsite_perm_required_decorator(self):

        @labsite_perm_required("staff")
        def my_view1(request, labsite):
            return labsite

        @labsite_perm_required("staff", "student")
        def my_view2(request, labsite):
            return labsite

        class Dummy(object):
            pass

        labsite = Labsite.objects.get(url_key='kaist-abcdef')
        request = Dummy()
        request.user = User.objects.get(id=10)
        request.user.del_row_perm(labsite, 'staff')
        request.user.del_row_perm(labsite, 'student')
        self.assertRaises(PermissionDenied, lambda: my_view1(request, 'kaist-abcdef'))
        self.assertRaises(PermissionDenied, lambda: my_view2(request, 'kaist-abcdef'))
        request.user.add_row_perm(labsite, 'staff')
        request.user.add_row_perm(labsite, 'student')
        labsite = my_view2(request, 'kaist-abcdef')
        self.assertEqual(labsite.url_key, 'kaist-abcdef')

class AdminTest(TestCase):
    fixtures = ['test-users.json', 'test-labsite-models.json']

    def setUp(self):
        settings.TESTING = True
        self.client.login(username='admin', password='acci')
        # Make sure Labsite.objects.count() works independently.
        Labsite.objects.all().delete()

    def tearDown(self):
        self.client.logout()
        settings.TESTING = False

    def test_approve_request(self):
        pk = 1
        new_request = NewRequest.objects.get(pk=pk)
        new_request.status = REQUEST_STATUS.UNREVIEWED
        new_request.save()
        response = self.client.post('/admin/labsite/newrequest/', {
            'action': 'approve_request',
            'index': 0,
            helpers.ACTION_CHECKBOX_NAME: pk,
        })
        self.failUnlessEqual(response.status_code, 200)
        self.assertContains(response, u'Course : CS101')
        self.assertTemplateUsed(response, 'labsite/admin/approve_new_request_confirmation.html')
        response = self.client.post('/admin/labsite/newrequest/', {
            'action': 'approve_request',
            'index': 0,
            helpers.ACTION_CHECKBOX_NAME: pk,
            'num_vm': new_request.num_vm + 1,
            'num_ip': 10,
            'post': 'yes',
        })
        self.failUnlessEqual(response.status_code, 302)
        self.assertEqual(NewRequest.objects.get(pk=pk).status, REQUEST_STATUS.APPROVED)
        self.assertEqual(Labsite.objects.count(), 1)
        self.assertEqual(Labsite.objects.get().num_vm, 101)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], u'test-user@nexr.co.kr')
    
    def test_deny_request(self):
        pk = 1
        new_request = NewRequest.objects.get(pk=pk)
        new_request.status = REQUEST_STATUS.UNREVIEWED
        new_request.save()
        response = self.client.post('/admin/labsite/newrequest/', {
            'action': 'deny_request',
            'index': 1,
            helpers.ACTION_CHECKBOX_NAME: pk,
        })
        self.failUnlessEqual(response.status_code, 200)
        self.assertContains(response, u'Course : CS101')
        self.assertTemplateUsed(response, 'labsite/admin/deny_new_request_confirmation.html')
        response = self.client.post('/admin/labsite/newrequest/', {
            'action': 'deny_request',
            'index': 1,
            helpers.ACTION_CHECKBOX_NAME: pk,
            'post': 'yes',
        })
        self.failUnlessEqual(response.status_code, 302)
        self.assertEqual(Labsite.objects.count(), 0)
        self.assertEqual(NewRequest.objects.get(pk=pk).status, REQUEST_STATUS.DENIED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], u'test-user@nexr.co.kr')

