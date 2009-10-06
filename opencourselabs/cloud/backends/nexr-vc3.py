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


import base64
from datetime import datetime
import hmac, hashlib
import operator
import urllib
import socket
import sys
from lxml import objectify
from lxml.etree import XMLSyntaxError
from urlparse import urlparse
from django.conf import settings
from opencourselabs.utils import iso8601
from opencourselabs.utils.httplib import HTTPConnection
from . import BaseAPI
from .. import CloudException, CloudQueryException

QUERYAPI_VERSION = '2009-07-10'
ISO8601_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
SIGNATURE_ALGORITHM = 'HmacSHA1'
SIGNATURE_VERSION = '2'

class BackendAPI(BaseAPI):

    def __init__(self, credentials=None):
        if credentials is None:
            self.credentials = {
                'access_key': settings.ICUBE_ACCESS_KEY,
                'secret_key': settings.ICUBE_SECRET_KEY,
            }
        else:
            self.credentials = credentials

    def run_instances(self, num, keypair_name, security_groups, image_id=None, instance_type=None):
        if image_id is None:
            image_id = settings.ICUBE_DEFAULT_IMAGE
        if instance_type is None:
            instance_type = settings.ICUBE_DEFAULT_TYPE
        kwargs = self._build_list_params('SecurityGroup', security_groups)
        status, reason, body = self._run_query('RunInstances', self.credentials,
            ImageId=image_id,
            MinCount=num,
            MaxCount=num,
            KeyName=keypair_name,
            #InstanceType=instance_type,
            **kwargs
        )
        try:
            response = objectify.fromstring(body)
        except XMLSyntaxError:
            self._handle_failures(body, status, reason, 'run_instance')
        if status == 200:
            result = {}
            instances = []
            for item in response.instancesSet.iterchildren():
                instances.append({
                    'instance_id': item.instanceId.text,
                    'state': (item.instanceState.code.pyval, item.instanceState.name.text),
                    'image_id': item.imageId.text,
                    'private_dns': item.privateDnsName.text,
                    'dns': item.dnsName.text,
                    'launch_index': item.amiLaunchIndex.pyval,
                    'launch_time': iso8601.parse_date(item.launchTime.text),
                })
            result['items'] = instances
            result['reservation_id'] = response.reservationId.text
            return result
        else:
            self._handle_failures(response, status, reason, 'run_instances')

    def create_instance_cluster(self, cluster_name, num, keypair_name, security_groups, image_id=None, instance_type=None):
        if image_id is None:
            image_id = settings.ICUBE_DEFAULT_IMAGE
        if instance_type is None:
            instance_type = settings.ICUBE_DEFAULT_TYPE
        kwargs = self._build_list_params('SecurityGroup', security_groups)
        status, reason, body = self._run_query('CreateInstanceCluster', self.credentials,
            ClusterName=cluster_name,
            ImageId=image_id,
            Count=num,
            KeyName=keypair_name,
            InstanceType=instance_type,
            **kwargs
        )
        try:
            response = objectify.fromstring(body)
        except XMLSyntaxError:
            self._handle_failures(body, status, reason, 'create_instance_cluster')
        if status == 200:
            result = {}
            instances = []
            for item in response.instancesSet.iterchildren():
                instances.append({
                    'instance_id': item.instanceId.text,
                    'state': (item.instanceState.code.pyval, item.instanceState.name.text),
                    'image_id': item.imageId.text,
                    'private_dns': item.privateDnsName.text,
                    'dns': item.dnsName.text,
                    'launch_index': item.amiLaunchIndex.pyval,
                    'launch_time': iso8601.parse_date(item.launchTime.text),
                })
            result['items'] = instances
            return result
        else:
            self._handle_failures(response, status, reason, 'create_instance_cluster')

    def create_hadoop_cluster(self, cluster_name, num, keypair_name, security_groups, image_id=None, instance_type=None, master_instance_type=None):
        if image_id is None:
            image_id = settings.ICUBE_DEFAULT_HADOOP_IMAGE
        kwargs = self._build_list_params('SecurityGroup', security_groups)
        result = {}
        instances = []

        # Run the slave nodes.
        status, reason, body = self._run_query('RunInstances', self.credentials,
            ImageId=image_id,
            MinCount=num - 1,
            MaxCount=num - 1,
            KeyName=keypair_name,
            InstanceType=instance_type if instance_type else settings.ICUBE_DEFAULT_TYPE,
            **kwargs
        )
        if status == 200:
            response_slaves = objectify.fromstring(body)
            for item in response_slaves.instancesSet.iterchildren():
                instances.append({
                    'instance_id': item.instanceId.text,
                    'state': (item.instanceState.code.pyval, item.instanceState.name.text),
                    'image_id': item.imageId.text,
                    'private_dns': item.privateDnsName.text,
                    'dns': item.dnsName.text,
                    'launch_index': item.amiLaunchIndex.pyval,
                    'launch_time': iso8601.parse_date(item.launchTime.text),
                })
        else:
            self._handle_failures(response, status, reason, 'create_hadoop_cluster')

        # Run the master node.
        status, reason, body = self._run_query('RunInstances', self.credentials,
            ImageId=image_id,
            MinCount=1,
            MaxCount=1,
            KeyName=keypair_name,
            InstanceType=master_instance_type if master_instance_type else settings.ICUBE_HADOOP_MASTER_TYPE,
            **kwargs
        )
        if status == 200:
            response_master = objectify.fromstring(body)
            for item in response_master.instancesSet.iterchildren():
                instances.append({
                    'instance_id': item.instanceId.text,
                    'state': (item.instanceState.code.pyval, item.instanceState.name.text),
                    'image_id': item.imageId.text,
                    'private_dns': item.privateDnsName.text,
                    'dns': item.dnsName.text,
                    'launch_index': item.amiLaunchIndex.pyval,
                    'launch_time': iso8601.parse_date(item.launchTime.text),
                })
                result['master'] = item.instanceId.text
        else:
            self._handle_failures(response, status, reason, 'create_hadoop_cluster')
        
        result['items'] = instances

        # The user should perform setup of Hadoop manually, bu running a given script 'install_hadoop.sh'.

        return result

    def delete_instance_cluster(self, cluster_name):
        status, reason, body = self._run_query('DeleteInstanceCluster', self.credentials, ClusterName=cluster_name)
        if status == 200:
            return True
        else:
            self._handle_failures(response, status, reason, 'delete_instance_cluster')

    def reboot_instances(self, instance_ids):
        kwargs = self._build_list_params('InstanceId', instance_ids)
        status, reason, body = self._run_query('RebootInstances', self.credentials, **kwargs)
        try:
            response = objectify.fromstring(body)
        except XMLSyntaxError:
            self._handle_failures(body, status, reason, 'reboot_instances')
        if status == 200:
            return True
        else:
            self._handle_failures(response, status, reason, 'reboot_instances')

    def terminate_instances(self, instance_ids):
        kwargs = self._build_list_params('InstanceId', instance_ids)
        status, reason, body = self._run_query('TerminateInstances', self.credentials, **kwargs)
        try:
            response = objectify.fromstring(body)
        except XMLSyntaxError:
            self._handle_failures(body, status, reason, 'terminate_instances')
        if status == 200:
            instances = []
            for item in response.instancesSet.iterchildren():
                instances.append({
                    'id': item.instanceId.text,
                    'shutdown_state': (item.shutdownState.code.pyval, item.shutdownState.name.text),
                    'previous_state': (item.previousState.code.pyval, item.previousState.name.text),
                })
            return instances
        else:
            self._handle_failures(response, status, reason, 'terminate_instances')

    def describe_instances(self, instance_ids):
        kwargs = self._build_list_params('InstanceId', instance_ids)
        status, reason, body = self._run_query('DescribeInstances', self.credentials, **kwargs)
        try:
            response = objectify.fromstring(body)
        except XMLSyntaxError:
            self._handle_failures(body, status, reason, 'describe_instances')
        if status == 200:
            instances = []
            for reservation in response.reservationSet.iterchildren():
                for item in reservation.instancesSet.iterchildren():
                    instances.append({
                        'instance_id': item.instanceId.text,
                        'state': (item.instanceState.code.pyval, item.instanceState.name.text),
                        'private_dns': item.privateDnsName.text,
                        'dns': item.dnsName.text,
                        'launch_index': item.amiLaunchIndex.pyval,
                        'launch_time': iso8601.parse_date(item.launchTime.text),
                        'keyname': item.keyName.text,
                        'type': item.instanceType.text,
                        'imageId': item.imageId.text,
                        'reason': item.reason.text,
                        'kernelId': item.kernelId.text,
                        'ramdiskId': item.ramdiskId.text,
                    })
            return instances
        else:
            self._handle_failures(response, status, reason, 'describe_instances')

    def allocate_address(self):
        status, reason, body = self._run_query('AllocateAddress', self.credentials)
        try:
            response = objectify.fromstring(body)
        except XMLSyntaxError:
            self._handle_failures(body, status, reason, 'allocate_address')
        if status == 200:
            return response.publicIp.text
        else:
            self._handle_failures(response, status, reason, 'allocate_address')

    def associate_address(self, instance_id, public_ip):
        status, reason, body = self._run_query('AssociateAddress', self.credentials,
            InstanceId=instance_id,
            PublicIp=public_ip
        )
        try:
            response = objectify.fromstring(body)
        except XMLSyntaxError:
            self._handle_failures(body, status, reason, 'associate_address')
        if status == 200:
            return True
        else:
            self._handle_failures(response, status, reason, 'associate_address')

    def disassociate_address(self, public_ip):
        status, reason, body = self._run_query('DisassociateAddress', self.credentials, PublicIp=public_ip)
        try:
            response = objectify.fromstring(body)
        except XMLSyntaxError:
            self._handle_failures(body, status, reason, 'disassociate_address')
        if status == 200:
            return True
        else:
            self._handle_failures(response, status, reason, 'disassociate_address')

    def release_address(self, public_ip):
        status, reason, body = self._run_query('ReleaseAddress', self.credentials, PublicIp=public_ip)
        try:
            response = objectify.fromstring(body)
        except XMLSyntaxError:
            self._handle_failures(body, status, reason, 'release_address')
        if status == 200:
            return True
        else:
            self._handle_failures(response, status, reason, 'release_address')

    def create_keypair(self, name):
        status, reason, body = self._run_query('CreateKeyPair', self.credentials, KeyName=name)
        try:
            response = objectify.fromstring(body)
        except XMLSyntaxError:
            self._handle_failures(body, status, reason, 'create_keypair')
        if status == 200:
            fingerprint = response.keyFingerprint.text
            material = response.keyMaterial.text
            return fingerprint, material
        else:
            self._handle_failures(response, status, reason, 'create_keypair')

    def describe_keypairs(self, names):
        kwargs = self._build_list_params('KeyName', names)
        status, reason, body = self._run_query('DescribeKeyPairs', self.credentials, **kwargs)
        try:
            response = objectify.fromstring(body)
        except XMLSyntaxError:
            self._handle_failures(body, status, reason, 'describe_keypair')
        if status == 200:
            keypairs = []
            for item in response.keySet.iterchildren():
                keypairs.append({
                    'name': item.keyName.text,
                    'fingerprint': item.keyFingerprint.text,
                })
            return keypairs
        else:
            self._handle_failures(response, status, reason, 'describe_keypairs')

    def delete_keypair(self, name):
        status, reason, body = self._run_query('DeleteKeyPair', self.credentials, KeyName=name)
        try:
            response = objectify.fromstring(body)
        except XMLSyntaxError:
            self._handle_failures(body, status, reason, 'delete_keypair')
        if status == 200:
            return True
        else:
            self._handle_failures(response, status, reason, 'delete_keypair')

    @staticmethod
    def _run_query(action, creds, **params):
        """
        Run an iCube query with given action and parameters.

        action -- A string that represents the name of desired action.
        params -- A dictionary that contains additional parameters according to action.
        access_key -- An API access key
        secret_key -- A key used in encryption for extra security
        """

        parts = urlparse(settings.ICUBE_REST_URL)
        host_for_request = parts.netloc
        host_for_signature = parts.hostname
        try:
            access_key = creds['access_key']
            secret_key = creds['secret_key']
        except KeyError:
            raise CloudException('iCube requires both access_key and secret_key in credentials.')

        current_time = datetime.now().strftime(ISO8601_DATETIME_FORMAT)
        query = [
            ('Action', action),
            ('Version', QUERYAPI_VERSION),
            ('AccessKeyId', access_key),
            ('Timestamp', current_time),
            ('SignatureMethod', SIGNATURE_ALGORITHM),
            ('SignatureVersion', SIGNATURE_VERSION),
        ]
        for key, value in params.iteritems():
            query.append((key, unicode(value).encode('utf8')))
        query.sort(key=operator.itemgetter(0))
        query_str = urllib.urlencode(query)

        signature = BackendAPI._make_signature(host_for_signature, parts.path, query_str, secret_key, SIGNATURE_ALGORITHM)
        query.append(('Signature', signature))
        query_str = urllib.urlencode(query)

        try:
            conn = HTTPConnection(host_for_request)
            conn.connect(timeout=10)
            conn.request('GET', parts.path + '?' + query_str)
            response = conn.getresponse()
            return response.status, response.reason, response.read()
        except socket.error, e:
            print>>sys.stderr, unicode(e)
            raise CloudQueryException({
                'where': 'run_query',
                'requestId': None, 
                'status': 500,
                'reason': u'Network Error: can\'t connect to the NexR iCube (%s)' % e,
                'errors': [],
            })
        finally:
            conn.close()

    @staticmethod
    def _build_list_params(name, values):
        args = {}
        for index, value in enumerate(values):
            args['%s.%d' % (name, index)] = value
        return args

    @staticmethod
    def _handle_failures(response, status, reason, where):
        errors = []
        requestId = '(None)'
        if isinstance(response, basestring):
            errors.append(u'XML syntax error in response. (maybe returned a HTML error page)')
        else:
            for item in response.Errors.iterchildren():
                try:
                    errors.append((item.Code.text, item.Message.text))
                except AttributeError:
                    pass
            requestId = response.RequestID.text,
        raise CloudQueryException({
            'where': where,
            'requestId': requestId,
            'status': status,
            'reason': reason,
            'errors': errors,
        })

    @staticmethod
    def _make_signature(host_for_signature, path, sorted_query_str, secret_key, algorithm):
        str_to_sign = 'GET\n' + host_for_signature + '\n' + path + '\n' + sorted_query_str
        return BackendAPI._calculate_rfc2104hmac(str_to_sign, secret_key, algorithm)

    @staticmethod
    def _calculate_rfc2104hmac(data, key, algorithm):
        assert algorithm.lower().startswith('hmac')
        hash_algorithm = algorithm[4:].lower()
        if hash_algorithm == 'sha1':
            hash_mod = hashlib.sha1
        elif hash_algorithm == 'sha256':
            hash_mod = hashlib.sha256
        else:
            raise CloudException('Unsupported hash algorithm: %s' % hash_algorithm)
        if key is None:
            raise CloudException('Cannot make signature because the secret key is not set.')
        mac = hmac.new(key, data, hash_mod)
        return base64.b64encode(mac.digest())
     
