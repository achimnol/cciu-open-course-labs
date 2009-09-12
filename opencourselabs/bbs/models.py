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
from django.db import connection, models


class Board(models.Model):
    belongs_to = models.ForeignKey('labsite.Labsite', blank=True, null=True)
    owner = models.ForeignKey('auth.User', blank=True, null=True)
    title = models.CharField(max_length=60)

    def __unicode__(self):
        if self.belongs_to is None:
            owner = self.owner
        else:
            owner = self.belongs_to
        return u'%s @%s' % (self.title, owner)

    class Meta:
        unique_together = ('belongs_to', 'title')

class Article(models.Model):
    belongs_to = models.ForeignKey('bbs.Board')
    tags = models.ManyToManyField('bbs.Tag', blank=True, null=True)
    title = models.CharField(max_length=120)
    author = models.ForeignKey('auth.User')
    written_at = models.DateTimeField(default=datetime.now)
    modified_at = models.DateTimeField(blank=True, null=True)
    is_notice = models.BooleanField(default=False, verbose_name=u'Mark as notice')
    attachments = models.ManyToManyField('repository.File', blank=True, null=True)
    body = models.TextField()

    def __unicode__(self):
        return u'%s @%s' % (self.title, self.belongs_to)

    class Meta:
        ordering = ('-is_notice', '-written_at',)

class Comment(models.Model):
    belongs_to = models.ForeignKey('bbs.Article')
    written_at = models.DateTimeField(default=datetime.now)
    author = models.ForeignKey('auth.User')
    body = models.TextField()

    def __unicode__(self):
        return u'by %s, at %s' % (self.author, self.written_at.strftime(u'%Y-%m-%d %H:%M:%S'))

    class Meta:
        ordering = ('written_at',)

class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)

    def __unicode__(self):
        return unicode(self.name)
