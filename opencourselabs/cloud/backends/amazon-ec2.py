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
from urlparse import urlparse
from django.conf import settings
from opencourselabs.utils import iso8601
from opencourselabs.utils.httplib import HTTPConnection
from . import BaseAPI
from .. import CloudException, CloudQueryException

QUERYAPI_VERSION = '2009-04-04'
ISO8601_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
SIGNATURE_ALGORITHM = 'HmacSHA1'
SIGNATURE_VERSION = '2'

class BackendAPI(BaseAPI):

    def __init__(self, credentials=None):
        if credentials is None:
            self.credentials = {
                'access_key': settings.EC2_ACCESS_KEY,
                'secret_key': settings.EC2_SECRET_KEY,
            }
        else:
            self.credentials = credentials

    def run_instances(self, num, keypair_name, security_groups, image_id=None, instance_type=None):
        if image_id is None:
            image_id = settings.EC2_DEFAULT_IMAGE
        if instance_type is None:
            instance_type = settings.EC2_DEFAULT_TYPE
        kwargs = self._build_list_params('SecurityGroup', security_groups)
        status, reason, body = self._run_query('RunInstances', self.credentials,
            ImageId=image_id,
            MinCount=1,
            MaxCount=num,
            KeyName=keypair_name,
            InstanceType=instance_type,
            **kwargs
        )
        response = objectify.fromstring(body)
        if status == 200:
            result = {}
            instances = []
            # TODO: where to use reservationId, ownerId and groupSet?
            for item in response.instancesSet.iterchildren():
                instances.append({
                    'instance_id': item.instanceId.text,
                    'state': (item.instanceState.code.pyval, item.instanceState.name.text),
                    'image_id': item.imageId.text,
                    'private_dns': item.privateDnsName.text,
                    'dns': item.dnsName.text,
                    'launch_index': item.amiLaunchIndex.pyval,
                    'launch_time': iso8601.parse_date(item.launchTime.text),
                    'placement': item.placement.availabilityZone.text,
                })
            result['items'] = instances
            result['reservation_id'] = response.reservationId
            return result
        else:
            self._handle_failures(response, status, reason, 'run_instances')

    def reboot_instances(self, instance_ids):
        kwargs = self._build_list_params('InstanceId', instance_ids)
        status, reason, body = self._run_query('RebootInstances', self.credentials, **kwargs)
        response = objectify.fromstring(body)
        if status == 200:
            return True
        else:
            self._handle_failures(response, status, reason, 'reboot_instances')

    def terminate_instances(self, instance_ids):
        kwargs = self._build_list_params('InstanceId', instance_ids)
        status, reason, body = self._run_query('TerminateInstances', self.credentials, **kwargs)
        response = objectify.fromstring(body)
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
        response = objectify.fromstring(body)
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
                        'placement': item.placement.availabilityZone.text,
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
        response = objectify.fromstring(body)
        if status == 200:
            return response.publicIp.text
        else:
            self._handle_failures(response, status, reason, 'allocate_address')

    def associate_address(self, instance_id, public_ip):
        status, reason, body = self._run_query('AssociateAddress', self.credentials,
            InstanceId=instance_id,
            PublicIp=public_ip
        )
        response = objectify.fromstring(body)
        if status == 200:
            return True
        else:
            self._handle_failures(response, status, reason, 'associate_address')

    def disassociate_address(self, public_ip):
        status, reason, body = self._run_query('DisassociateAddress', self.credentials, PublicIp=public_ip)
        response = objectify.fromstring(body)
        if status == 200:
            return True
        else:
            self._handle_failures(response, status, reason, 'disassociate_address')

    def release_address(self, public_ip):
        status, reason, body = self._run_query('ReleaseAddress', self.credentials, PublicIp=public_ip)
        response = objectify.fromstring(body)
        if status == 200:
            return True
        else:
            self._handle_failures(response, status, reason, 'release_address')

    def create_keypair(self, name):
        status, reason, body = self._run_query('CreateKeyPair', self.credentials, KeyName=name)
        response = objectify.fromstring(body)
        if status == 200:
            fingerprint = response.keyFingerprint.text
            material = response.keyMaterial.text
            return fingerprint, material
        else:
            self._handle_failures(response, status, reason, 'create_keypair')

    def describe_keypairs(self, names):
        kwargs = self._build_list_params('KeyName', names)
        status, reason, body = self._run_query('DescribeKeyPairs', self.credentials, **kwargs)
        response = objectify.fromstring(body)
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
        response = objectify.fromstring(body)
        if status == 200:
            return True
        else:
            self._handle_failures(response, status, reason, 'delete_keypair')

    @staticmethod
    def _run_query(action, creds, **params):
        """
        Run an EC2 query with given action and parameters.

        action -- A string that represents the name of desired action.
        params -- A dictionary that contains additional parameters according to action.
        access_key -- An API access key
        secret_key -- A key used in encryption for extra security
        """

        parts = urlparse(settings.EC2_REST_URL)
        host_for_request = parts.netloc
        host_for_signature = parts.hostname
        try:
            access_key = creds['access_key']
            secret_key = creds['secret_key']
        except KeyError:
            raise CloudException('EC2 requires both access_key and secret_key in credentials.')

        current_time = datetime.now().strftime(ISO8601_DATETIME_FORMAT)
        query = [
            ('Action', action),
            ('Version', QUERYAPI_VERSION),
            ('AWSAccessKeyId', access_key),
            ('Expires', current_time),
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
            conn.request('GET', parts.path + '?' + query_str)
            response = conn.getresponse()
            return response.status, response.reason, response.read()
        except Exception, e:
            raise CloudQueryException({
                'where': 'run_query',
                'requestId': response.RequestID.text,
                'status': 500,
                'reason': u'Network Error: can\'t connect to the Amazon EC2 (%s %s)' % (type(e), e.message),
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
        for item in response.Errors.iterchildren():
            try:
                errors.append((item.Code.text, item.Message.text))
            except AttributeError:
                pass
        raise CloudQueryException({
            'where': where,
            'requestId': response.RequestID.text,
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
 
