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
from opencourselabs.cloud.models import Backend, InstanceGroup

class Command(BaseCommand):
    help = u'''Cleans up untracked instances, such as broken ones.'''

    def handle(self, *args, **options):

        for backend in Backend.objects.all():
            print u'Checking backend %s...' % backend
            cloud = backend.get_api()
            print '- Retrieving all keypairs from the cloud...'
            all_keypairs = set([item['name'] for item in cloud.describe_keypairs([]) if item['name'].startswith('cciu-')])
            print '  %s' % ', '.join(all_keypairs)
            print '- Retrieving all registered keypairs...'
            valid_keypairs = set([row[0] for row in InstanceGroup.objects.filter(backend=backend).values_list('keypair_name')])
            print '  %s' % ', '.join(valid_keypairs)
            print '- Deleting unregistered keypairs in the cloud...'
            invalid_keypairs = all_keypairs - valid_keypairs
            for name in invalid_keypairs:
                try:
                    print '    (%s)' % name
                    cloud.delete_keypair(name)
                except CloudQueryException, e:
                    print>>sys.stderr, '%s: %s' % (e, e.detail['errors'])


