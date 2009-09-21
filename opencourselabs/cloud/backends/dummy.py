#-*- encoding: utf8 -*-

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
from django.conf import settings
from . import BaseAPI

def _create_random_slug(length):
    return ''.join([random.choice('abcdefghijklnopqrstuvxyz123456789') for j in xrange(length)])

class BackendAPI(BaseAPI):

    def __init__(self, credentials=None):
        self.mock_instances = {}
        self.mock_keypairs = {}

    def run_instances(self, num, keypair_name, security_groups, image_id=None, instance_type=None):
        if image_id is None:
            image_id = settings.EC2_DEFAULT_IMAGE
        if instance_type is None:
            instance_type = settings.EC2_DEFAULT_TYPE
        items = []
        for i in xrange(num):
            id = 'i-%s' % _create_random_slug(12)
            instance = {
                'instance_id': id,
                'state': (16, 'running'),
                'image_id': image_id,
                'private_dns': '%s.test.cloud' % id,
                'dns': '%s.test.cciu.or.kr' % id,
                'launch_index': i,
                'launch_time': datetime.now(),
                'placement': 'NexR VC3 (South Korea)',
            }
            items.append(instance)
            self.mock_instances[id] = instance
        result = {
            'items': items,
            'reservation_id': 'r-%s' % _create_random_slug(12),
        }
        return result
        
    def reboot_instances(self, instance_ids):
        for id in instance_ids:
            instance = self.mock_instances[id]
            # do nothing
        return True

    def terminate_instances(self, instance_ids):
        result = []
        for id in instance_ids:
            item = {
                'instance_id': id,
                'shutdown_state': (32, 'shutting down'),
                'previous_state': (16, 'running'),
            }
            result.append(item)
            del self.mock_instances[id]
        return result

    def describe_instances(self, instance_ids):
        result = []
        for id in instance_ids:
            instance = sel.mock_instances[id]
            item = {
                'instance_id': id,
                'state': (16, 'running'),
                'private_dns': instance['private_dns'],
                'dns': instance['dns'],
                'launch_index': instance['launch_index'],
                'launch_time': instance['launch_time'],
                'type': 'm1.small',
                'placement': instance['placement'],
                'imageId': 'ami-1234567890',
                'reason': '',
                'kernelId': 'ker-1234567890',
                'ramdiskId': 'rdk-1234567890',
            }
            result.append(item)
        return result

    def create_keypair(self, name):
        keypair = {
            'fingerprint': ':'.join([hex(random.randint(0,16)) for i in xrange(16)]),
            'material': _create_random_slug(256),
        }
        self.mock_keypairs[name] = keypair
        return keypair['fingerprint'], keypair['material']

    def delete_keypair(self, name):
        del self.mock_keypair[name]
