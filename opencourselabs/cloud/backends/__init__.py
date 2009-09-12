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

from .. import CloudException

class BaseAPI(object):
    """The definition for public interface of cloud API backends.
    Every required method should be overrided and implemented in subclasses."""
    
    def __init__(self, credentials=None):
        pass
    
    def run_instances(self, num, keypair_name, security_groups, image_id=None, instance_type=None):
        raise NotImplementedError()

    def create_instance_cluster(self, cluster_name, num, keypair_name, security_groups, image_id=None, instance_type=None):
        raise NotImplementedError()

    def create_hadoop_cluster(self, cluster_name, num, keypair_name, security_groups, image_id=None, instance_type=None):
        raise NotImplementedError()

    def delete_instance_cluster(self, cluster_name):
        raise NotImplementedError()

    def reboot_instances(self, instance_ids):
        raise NotImplementedError()

    def terminate_instaces(self, instance_ids):
        raise NotImplementedError()

    def describe_instances(self, instance_ids):
        raise NotImplementedError()

    def allocate_address(self):
        raise NotImplementedError()

    def associate_address(self, instance_id, public_ip):
        raise NotImplementedError()

    def disassociate_address(self, public_ip):
        raise NotImplementedError()

    def release_address(self, public_ip):
        raise NotImplementedError()

    def create_keypair(self, name):
        raise NotImplementedError()

    def descrie_keypairs(self, names):
        raise NotImplementedError()

    def delete_keypair(self, name):
        raise NotImplementedError()
