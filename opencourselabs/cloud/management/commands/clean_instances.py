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


from optparse import make_option
import sys
from django.conf import settings
from django.core.management.base import BaseCommand
from opencourselabs.cloud import CloudQueryException
from opencourselabs.cloud.models import Backend, Instance, InstanceGroup

class Command(BaseCommand):
    help = u'''Cleans up untracked instances, such as broken ones.'''

    def handle(self, *args, **options):

        for backend in Backend.objects.all():
            print u'Checking backend %s...' % backend
            cloud = backend.get_api()
            print '- Retrieving all instances from the cloud...'
            all_instances = set([item['instance_id'] for item in cloud.describe_instances([]) if item['state'][0] not in (0, 32, 48) and item['keyname'].startswith('cciu-')])
            print '  %s' % ', '.join(all_instances)
            print '- Retrieving all registered instances...'
            valid_instances = set([row[0] for row in Instance.objects.filter(belongs_to__backend=backend).values_list('instance_id')])
            print '  %s' % ', '.join(valid_instances)
            invalid_instances = all_instances - valid_instances
            print '- Terminating unregistered instances in the cloud...'
            print '  %s' % ', '.join(invalid_instances)
            try:
                cloud.terminate_instances([instance_id for instance_id in invalid_instances])
            except CloudQueryException, e:
                print>>sys.stderr, '%s: %s' % (e, e.detail['errors'])


