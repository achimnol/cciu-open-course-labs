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
import pprint
from django.core.management.base import BaseCommand
from ...models import Backend

class Command(BaseCommand):
    help = u'''Shows all instances created by CCI:U, even including terminated and un-tracked ones.'''

    def handle(self, *args, **options):

        for backend in Backend.objects.all():
            print u'Checking backend %s...' % backend
            cloud = backend.get_api()
            all_instances = [(item['instance_id'], item['state'][1], item['keyname']) for item in cloud.describe_instances([]) if item['keyname'].startswith('cciu-')]
            pprint.pprint(all_instances, indent=2, width=75)
