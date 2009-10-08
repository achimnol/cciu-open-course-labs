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
import uuid
from django.db import models
from django.db.models.signals import post_delete
from django.conf import settings
from opencourselabs.cloud import CloudException
from opencourselabs.utils import fields, Enumeration
from . import CloudQueryException

BACKEND_TYPES = Enumeration([
    ('amazon-ec2', 'EC2', u'Amazon EC2 (US)'),
    ('nexr-vc3', 'ICUBE', u'NexR iCube'),
])
INSTANCEGROUP_TYPES = Enumeration([
    (0, 'NORMAL', u'Normal'),
    (1, 'HADOOP_CLUSTER', u'Hadoop cluster'),
])

def get_api(backend_name, credentials=None):
    backend_name = 'backends.' + backend_name
    try:
        if getattr(settings, 'TESTING', False):
            mod = __import__('backends.dummy', globals(), locals(), ['BackendAPI'], 1)
        else:
            mod = __import__(backend_name, globals(), locals(), ['BackendAPI'], 1)
    except ImportError:
        raise CloudException(u'Backend %s is not supported.' % backend_name)
    else:
        return mod.BackendAPI(credentials=credentials)

class Backend(models.Model):
    name = models.CharField(max_length=12, choices=BACKEND_TYPES)
    credentials = fields.JSONField(blank=True, null=True)

    def supports_hadoop_deploy(self):
        if self.name == u'nexr-vc3':
            return True
        return False

    def get_default_security_group(self):
        if self.name == u'amazon-ec2':
            return settings.EC2_DEFAULT_SECURITYGROUP
        elif self.name == u'nexr-vc3':
            return settings.ICUBE_DEFAULT_SECURITYGROUP

    def get_api(self):
        # Perform a relative import in the current package.
        # For example, when name is 'vc3', opencourselabs.cloud.backends.vc3 is imported.
        backend_name = 'backends.' + self.name
        try:
            if getattr(settings, 'TESTING', False):
                mod = __import__('backends.dummy', globals(), locals(), ['BackendAPI'], 1)
            else:
                mod = __import__(backend_name, globals(), locals(), ['BackendAPI'], 1)
        except ImportError:
            raise CloudException(u'Backend %s is not supported.' % self.name)
        else:
            return mod.BackendAPI(credentials=self.credentials)

    def __unicode__(self):
        try:
            access_identifier = self.credentials['access_key']
        except (KeyError, TypeError):
            access_identifier = u'(Default)'
        return u'%s:%s' % (self.name, access_identifier)

class InstanceGroup(models.Model):
    """
    A model and also controller for real VM instances in the cloud.
    You have to instantiate this model and save it to the database first,
    and then you may call run().
    """
    backend = models.ForeignKey('cloud.Backend')
    belongs_to = models.ForeignKey('labsite.Team', related_name='instance_group', unique=True, blank=True, null=True)
    num_instances = models.PositiveIntegerField()
    keypair_name = models.CharField(max_length=40)
    security_group = models.CharField(max_length=32)
    private_key = models.TextField()
    type = models.SmallIntegerField(default=INSTANCEGROUP_TYPES.NORMAL, choices=INSTANCEGROUP_TYPES)
    cluster_name = models.CharField(max_length=40, blank=True, null=True)
    master = models.ForeignKey('cloud.Instance', blank=True, null=True, related_name='master_group')

    def __unicode__(self):
        return u'%d @%s' % (self.id, self.backend)

    def run(self, append=-1):
        cloud = self.backend.get_api()
        if self.type == INSTANCEGROUP_TYPES.HADOOP_CLUSTER:
            # We should always destroy all the current instances of this group to deploy Hadoop.
            self.terminate(delete_myself=False)
            if append < 0:
                append = 0
            self.cluster_name = 'cciu-c-%s' % uuid.uuid4().hex
            result = cloud.create_hadoop_cluster(self.cluster_name, self.num_instances + append, self.keypair_name, self.security_group.split(','))
            self.type = INSTANCEGROUP_TYPES.HADOOP_CLUSTER
            self.num_instances = len(result['items'])
            self.save()
        else:
            if append == -1:
                # Creates a new instance group.
                result = cloud.run_instances(self.num_instances, self.keypair_name, self.security_group.split(','))
                self.num_instances = len(result['items'])
            elif append > 0:
                # Adds new instances to this group.
                result = cloud.run_instances(append, self.keypair_name, self.security_group.split(','))
                self.num_instances += len(result['items'])
            self.save()
        # Adds information of new instances.
        for item in result['items']:
            instance = Instance()
            instance.belongs_to = self
            instance.instance_id = item['instance_id']
            instance.image_id = item['image_id']
            instance.save()
        if self.type == INSTANCEGROUP_TYPES.HADOOP_CLUSTER:
            self.master = Instance.objects.get(instance_id=result['master'])
            self.save()

    def reboot(self):
        cloud = self.backend.get_api()
        instance_ids = []
        for instance in self.instance_set.all():
            instance_ids.append(instance.instance_id)
        cloud.reboot_instances(instance_ids)

    def terminate(self, delete_myself=True):
        cloud = self.backend.get_api()
        #if self.cluster_name is not None and len(self.cluster_name) > 0:
        #    cloud.delete_instance_cluster(self.cluster_name)
        #    self.cluster_name = None
        #else:
        instance_ids = []
        for instance in self.instance_set.all():
            instance_ids.append(instance.instance_id)
        cloud.terminate_instances(instance_ids)
        if delete_myself:
            self.instance_set.all().delete()
            self.delete()
        else:
            self.master = None
            self.save()
            self.instance_set.all().delete()

    def describe(self):
        cloud = self.backend.get_api()
        instance_ids = []
        for instance in self.instance_set.all():
            instance_ids.append(instance.instance_id)
        result = cloud.describe_instances(instance_ids)
        for instance in self.instance_set.all():
            for item in result:
                if instance.instance_id == item['instance_id']:
                    item['elastic_ip'] = instance.elastic_ip
                    break
            else:
                missing_item = defaultdict(lambda: None)
                missing_item.update({
                    'instance_id': instance.instance_id,
                    'state': (1600, u'Missing!'),
                })
                result.append(missing_item)
        return result

class Instance(models.Model):
    belongs_to = models.ForeignKey(InstanceGroup, related_name='instance_set')
    instance_id = models.CharField(max_length=32)
    image_id = models.CharField(max_length=32)
    elastic_ip = models.CharField(max_length=40, blank=True, null=True)
    
    def delete(self):
        # This should not delete the instance group object.
        # (Django's default behaviour is similar to ON DELETE CASCADE.)
        self.master_group.clear()
        super(Instance, self).delete()

    def __unicode__(self):
        return u'VMInstance(%s)' % self.instance_id

    def reboot(self):
        cloud = self.belongs_to.backend.get_api()
        cloud.reboot_instances([self.instance_id])

    def describe(self):
        cloud = self.belongs_to.backend.get_api()
        result = cloud.describe_instances([self.instance_id])
        result[0]['elastic_ip'] = self.elastic_ip
        return result

    def allocate_ip(self):
        if self.elastic_ip is not None:
            return self.elastic_ip
        cloud = self.belongs_to.backend.get_api()
        ip = cloud.allocate_address()
        cloud.associate_address(self.instance_id, ip)
        self.elastic_ip = ip
        self.save()
        return ip

    def release_ip(self):
        if self.elastic_ip is None:
            return
        cloud = self.belongs_to.backend.get_api()
        cloud.disassociate_address(self.elastic_ip)
        cloud.release_address(self.elastic_ip)
        self.elastic_ip = None
        self.save()


def describe_instances(cloud, instance_ids):
    # Here, we may be asked to retreive a subset or cross-set of
    # instances in one or more instance groups, so we have to do it
    # manually.
    result = cloud.describe_instances(instance_ids)
    instances = Instance.objects.filter(instance_id__in=instance_ids)
    for instance in instances:
        for item in result:
            if item['instance_id'] == instance.instance_id:
                # Adds additional info from our database.
                item['id'] = instance.id
                item['elastic_ip'] = instance.elastic_ip
                break
        else:
            missing_item = defaultdict(lambda: None)
            missing_item.update({
                'instance_id': instance.instance_id,
                'id': instance.id,
                'state': (1600, u'Missing!'),
            })
            result.append(missing_item)
    return result

def instance_post_delete_handler(sender, **kwargs):
    instance = kwargs['instance']
    try:
        cloud = instance.belongs_to.backend.get_api()
    except:
        return
    try:
        cloud.terminate_instances([instance.instance_id])
    except CloudQueryException, e:
        # This may be called twice.
        pass
    if instance.elastic_ip is not None:
        try:
            cloud.release_address(instance.elastic_ip)
        except CloudQueryException, e:
            pass

post_delete.connect(instance_post_delete_handler, sender=Instance)
