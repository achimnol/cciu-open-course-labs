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


import os, os.path, sys
import glob
import tempfile
from datetime import datetime, timedelta
from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand
from opencourselabs.repository.models import UploadTempFile

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--slient', action='store_true', dest='silent', help=u'If on, console output will be suppressed. Useful for cron jobs.', default=False),
        make_option('--timesince', dest='timesince', help=u'You may set how old the temp records should be in seconds.', default=7200),
    )
    help = u'''Cleans up temporary files created by multiple-upload components.
By default, only at least 2 hours old files are deleted.'''

    def handle(self, *args, **options):
        silent = options['silent']
        min_age = int(options['timesince'])
        now = datetime.now()

        if silent:
            old_stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')

        print u'Starting clean-up temporary upload files...'
        temp_records = UploadTempFile.objects.filter(started_at__lt=now - timedelta(seconds=min_age))
        for file in temp_records:
            print u'Checking tracked record %s (%s)...' % (file.key, file.started_at.strftime('%Y-%m-%d %H:%M:%S'))
            if os.path.isfile(file.saved_path):
                print u'  Deleting %s (%s)...' % (file.saved_path, file.original_name)
                os.remove(file.saved_path)
        temp_records.delete()

        print u'Checking non-tracked temporary upload files...'
        for filename in glob.glob(os.path.join(tempfile.gettempdir(), 'tmp*-cciu-uploadtemp')):
            print u'  Deleting %s...' % os.path.basename(filename)
            os.remove(filename)

        print u'OK.'
        if silent:
            sys.stdout = old_stdout

