#! /usr/bin/env python
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


"""
An EC2 Query Tester Script

Authentication parameters are read from settings.
We recommend you to put them in settings_local.py.

Usage:
    ./ec2-query.py Action [Param1=Value Param2=Value ...]

Example:
    ./ec2-query.py CreateKeyPair KeyName=my-key
    ./ec2-query.py RunInstance ImageId=ami-1234568 MinCount=1 MaxCount=2 KeyName=my-key

Required authentication parameters:
    EC2_HOST, EC2_ACCESS_KEY, EC2_SECRET_KEY
"""

from django.core.management import setup_environ
import settings
setup_environ(settings)

import getopt, sys, os
from lxml import etree
from django.conf import settings
from opencourselabs.cloud.models import get_api

# Use NexR test account in the settings.
# (If no credentials are given, it will use the default ones.)
cloud = get_api(sys.argv[1])

def run_action(action, params):
    status, reason, body = cloud._run_query(action, cloud.credentials, **params)
    print status, reason
    tree = etree.fromstring(body)
    print etree.tostring(tree, pretty_print=True)


params = {}
if len(sys.argv) > 3:
	for arg in sys.argv[3:]:
		key, value = arg.split('=', 1)
		params[key] = value

run_action(sys.argv[2], params)
