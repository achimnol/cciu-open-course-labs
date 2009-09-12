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
import httplib
import operator
import urllib

QUERYAPI_VERSION = '2009-04-04'
ISO8601_DATETIME_FORMAT = '%Y-%m-%dT%TZ'
SIGNATURE_ALGORITHM = 'HmacSHA1'
SIGNATURE_VERSION = '2'

class EC2QueryException(Exception):
    pass

def run_query(host_for_request, host_for_signature, action, params, access_key, secret_key):
    """
    Run an EC2 query with given action and parameters.

    host_for_request -- 
    host_for_signature --
    action -- A string that represents the name of desired action.
    params -- A dictionary that contains additional parameters according to action.
    access_key -- An API access key
    secret_key -- A key used in encryption for extra security
    """

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
        query.append((key, value))
    query.sort(key=operator.itemgetter(0))
    query_str = urllib.urlencode(query)

    signature = _make_signature(host_for_signature, query_str, secret_key, SIGNATURE_ALGORITHM)
    query.append(('Signature', signature))
    query_str = urllib.urlencode(query)

    try:
        conn = httplib.HTTPConnection(host_for_request)
        conn.request('GET', '/?' + query_str)
        response = conn.getresponse()
        return response.status, response.reason, response.read()
    except Exception, e:
        raise EC2QueryException(e.message)
    finally:
        conn.close()

def validate_query(host_for_signature, query_str, secret_key):
    pass

def validate_query_with_params(host_for_signature, params, secret_key):
    pass

def _make_signature(host_for_signature, sorted_query_str, secret_key, algorithm):
    str_to_sign = 'GET\n' + host_for_signature + '\n/\n' + sorted_query_str
    return _calculate_rfc2104hmac(str_to_sign, secret_key, algorithm)

def _calculate_rfc2104hmac(data, key, algorithm):
    assert algorithm.lower().startswith('hmac')
    hash_algorithm = algorithm[4:].lower()
    if hash_algorithm == 'sha1':
        hash_mod = hashlib.sha1
    elif hash_algorithm == 'sha256':
        hash_mod = hashlib.sha256
    else:
    	raise EC2QueryException('Unsupported hash algorithm: %s' % hash_algorithm)
    mac = hmac.new(key, data, hash_mod)
    return base64.b64encode(mac.digest())
 
