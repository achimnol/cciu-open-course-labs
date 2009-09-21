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
import random
from django.contrib.admin import helpers
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Sum, Q
from django.db.models.signals import post_save
from django.shortcuts import render_to_response
from django.template import RequestContext
from opencourselabs.cloud.models import BACKEND_TYPES
from opencourselabs.utils import Enumeration

ORGANIZATIONS = (
    (u'kaist', u'KAIST'),
    (u'nexr', u'NexR'),
    #(u'snu', u'Seoul National University'),
)
REQUEST_STATUS = Enumeration([
    (0, 'UNREVIEWED', u'Unreviewed'),
    (1, 'DENIED', u'Denied'),
    (2, 'APPROVED', u'Approved'),
])

class NewRequest(models.Model):
    creator = models.ForeignKey('auth.User')
    title = models.CharField(max_length=60, verbose_name=u'Course Title')
    course = models.CharField(max_length=60, verbose_name=u'Course Code',
        help_text=u'Enter the course code as in your organization. (eg. CS101)')
    description = models.TextField()
    organization = models.CharField(max_length=30, choices=ORGANIZATIONS)
    cloud = models.CharField(max_length=12, choices=BACKEND_TYPES,
        help_text=u'NOTE: Support for Amazon EC2 is experimental currently.')
    access_key = models.CharField(max_length=20, blank=True, null=True,
        help_text=u'The access key for your AWS account.')
    secret_key = models.CharField(max_length=40, blank=True, null=True,
        help_text=u'The secret key for your AWS account.')
    num_vm = models.IntegerField(verbose_name=u'Number of VMs', default=1,
        help_text=u'Enter the number of VM instances you would want to use.')
    num_ip = models.IntegerField(verbose_name=u'Number of IPs', default=1,
        help_text=u'Enter the number of public IPs you would want to use. VM instances have private IPs only by default, but you can allocate them public IPs explicitly.')
    period_begin = models.DateField()
    period_end = models.DateField()
    additional_question1 = models.CharField(verbose_name=u'Additional question 1', max_length=200, blank=True,
        help_text=u'This question is displayed when a student requests to join.')
    additional_question2 = models.CharField(verbose_name=u'Additional question 2', max_length=200, blank=True)
    contact_cellphone = models.CharField(verbose_name=u'Contact (cellphone)', max_length=20,
        help_text=u'To get more information about the request or inform emergent situations, the service operator may call you.')
    contact_alternative = models.CharField(verbose_name=u'Contact (alternative)', max_length=60, blank=True,
        help_text=u'If we fail to call via your cellphone, we may try this one alternatively.')
    status = models.SmallIntegerField(default=0, choices=REQUEST_STATUS)
    created_at = models.DateTimeField(default=datetime.now)
    approved_at = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return u'%s: [%s] %s' % (self.get_organization_display(), self.course, self.title)

    class Meta:
        verbose_name = 'Request for New Course Lab'
        verbose_name_plural = 'Requests for New Course Lab'

class Labsite(models.Model):
    url_key = models.CharField(max_length=32, unique=True)
    owner = models.ForeignKey('auth.User', related_name='owned_labsite_set')
    title = models.CharField(max_length=60)
    course = models.CharField(max_length=60)
    description = models.CharField(max_length=200)
    organization = models.CharField(max_length=30, choices=ORGANIZATIONS)
    cloud = models.CharField(max_length=12, choices=BACKEND_TYPES)
    access_key = models.CharField(max_length=20, blank=True, null=True)
    secret_key = models.CharField(max_length=40, blank=True, null=True)
    num_ip = models.IntegerField(default=0)
    num_vm = models.IntegerField(default=0)
    additional_question1 = models.CharField(max_length=200, blank=True)
    additional_question2 = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=datetime.now)
    period_begin = models.DateField()
    period_end = models.DateField()
    is_active = models.BooleanField(default=True)
    contact_cellphone = models.CharField(max_length=20)
    contact_alternative = models.CharField(max_length=60, blank=True)

    def __unicode__(self):
        return u'%s' % self.url_key

    def save(self, *args, **kwargs):
        if self.id is None or self.id == 0:
            self.url_key = u'%s-%s' % (
                self.organization,
                u''.join([random.choice(u'abcdefghijklmnpqurstuvwxyz023456789') for i in xrange(6)])
            )
        super(Labsite, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('labsite.views.dashboard', [str(self.url_key)])

    def organization_name(self):
        return self.get_organization_display()

    def get_num_allocated_instances(self):
        """Get the number of currently allocated instances to all teams that belong to this labsite.
        This value is less than or equivalent to self.num_vm."""
        num_occupied = Team.objects.filter(belongs_to=self).aggregate(sum=Sum('num_vm'))['sum']
        if num_occupied is None:
            num_occupied = 0
        return num_occupied

    def get_all_staffs(self):
        return User.objects.filter(
            row_permission_set__name='staff',
            row_permission_set__object_id=self.id,
            row_permission_set__content_type=ContentType.objects.get_for_model(self),
            is_active=True,
        )

    def get_all_students(self):
        return User.objects.filter(
            row_permission_set__name='student',
            row_permission_set__object_id=self.id,
            row_permission_set__content_type=ContentType.objects.get_for_model(self),
            is_active=True,
        )

    def get_all_members(self):
        return User.objects.filter(
            Q(row_permission_set__name='staff') | Q(row_permission_set__name='student'),
            row_permission_set__object_id=self.id,
            row_permission_set__content_type=ContentType.objects.get_for_model(self),
            is_active=True,
        )

    def get_backend_credentials(self):
        if self.access_key is None or self.access_key == '':
            return None
        return {
            'access_key': self.access_key,
            'secret_key': self.secret_key,
        }

    class Meta:
        verbose_name = u'Course Lab'

class JoinRequest(models.Model):
    owner = models.ForeignKey('auth.User')
    labsite = models.ForeignKey('labsite.Labsite')
    additional_answer1 = models.CharField(max_length=200, blank=True)
    additional_answer2 = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=datetime.now)

class Team(models.Model):
    name = models.CharField(max_length=30)
    belongs_to = models.ForeignKey('labsite.Labsite')
    members = models.ManyToManyField('auth.User')
    use_hadoop = models.BooleanField(help_text=u'This option automatically deploys a Hadoop cluster.')
    num_vm = models.IntegerField(default=0, verbose_name=u'Number of VMs')

    def __unicode__(self):
        return u'%s @%s' % (self.name, self.belongs_to.url_key)

    class Meta:
        unique_together = (('name', 'belongs_to'),)


def labsite_post_save_handler(sender, **kwargs):
    labsite = kwargs['instance']
    if labsite.is_active == False:
        from opencourselabs.cloud import CloudQueryException
        from opencourselabs.cloud.models import InstanceGroup, Instance, get_api # Avoid a circular dependency
        instance_groups = InstanceGroup.objects.filter(belongs_to__belongs_to=labsite)
        instance_groups.update(num_instances=0)
        deactivated_instances = Instance.objects.filter(belongs_to__belongs_to__belongs_to=labsite)
        cloud = get_api(labsite.cloud, labsite.get_backend_credentials())
        try:
            if deactivated_instances.count() > 0:
                cloud.terminate_instances([instance.instance_id for instance in deactivated_instances])
        except CloudQueryException, e:
            pass
        deactivated_instances.delete()


post_save.connect(labsite_post_save_handler, sender=Labsite)
