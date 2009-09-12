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


from datetime import datetime
from django.db import models
from opencourselabs.utils import Enumeration

ASSIGNMENT_TYPES = Enumeration([
    (0, 'INDIVIDUAL', u'For individuals'),
    (1, 'TEAM', u'For teams'),
])

class Assignment(models.Model):
    belongs_to = models.ForeignKey('labsite.Labsite')
    name = models.CharField(max_length=120)
    description = models.TextField()
    type = models.SmallIntegerField(choices=ASSIGNMENT_TYPES)
    due_date = models.DateTimeField()
    repos_dir = models.ForeignKey('repository.Directory')
    attachments = models.ManyToManyField('repository.File', blank=True, null=True)

    def __unicode__(self):
        return u'%s (Due: %s)' % (self.name, self.due_date)

class Submission(models.Model):
    belongs_to = models.ForeignKey(Assignment, related_name='submission_set')
    description = models.TextField()
    submitted = models.DateTimeField(default=datetime.now)
    submitter = models.ForeignKey('auth.User')
    team = models.ForeignKey('labsite.Team', blank=True, null=True)
    attachments = models.ManyToManyField('repository.File', blank=True, null=True)

    def __unicode__(self):
        return u'%s by %s' % (self.belongs_to.name, self.submitter if self.belongs_to.type == 0 else self.team.name)

def check_user_submission(assignment, user):
    if user.is_authenticated():
        count = Submission.objects.filter(belongs_to=assignment, submitter=user).count()
        return count > 0
    return False
    
def check_team_submission(assignment, team):
    if team is not None:
        count = Submission.objects.filter(belongs_to=assignment, team=team).count()
        return count > 0
    return False

