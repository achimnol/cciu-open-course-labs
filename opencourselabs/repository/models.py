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
import os, os.path, sys
from django.conf import settings
from django.db import models
from opencourselabs.utils import Enumeration
from opencourselabs.utils.fields import JSONField

DIRECTORY_TYPES = Enumeration([
    (0, 'PUBLIC', 'public'),
    (1, 'PRIVATE', 'private'),
    (2, 'SYSTEM', 'system'),
])
PATHSEP = u'/'

class RepositoryError(Exception):
    pass

class Directory(models.Model):
    # The name of a real directory in the file system is just the id value of this model instance.
    # IMPORTANT: Don't create or delete Directory object directly.
    #            Use create_directory and delete_directory functions below.
    domain = models.CharField(max_length=60)
    name = models.CharField(max_length=60)
    type = models.SmallIntegerField(choices=DIRECTORY_TYPES)
    created_at = models.DateTimeField(default=datetime.now)
    description = models.CharField(max_length=200)
    real_path = models.CharField(max_length=512)
    parent = models.ForeignKey('repository.Directory', blank=True, null=True)

    def __init__(self, *args, **kwargs):
        self._real_path = u''
        return super(Directory, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % self.get_real_path()

    def get_real_path(self):
        if os.path.isdir(self.real_path):
            return self.real_path
        else:
            # Process path changes of the whole repository.
            new_repos_path = os.path.join(settings.REPOSITORY_STORAGE_PATH, self.domain)
            if os.path.isdir(new_repos_path):
                path_parts = self.real_path.split(os.sep)
                for i, name in enumerate(path_parts):
                    if name == self.domain:
                        self.real_path = os.path.join(settings.REPOSITORY_STORAGE_PATH, *path_parts[i:])
                        self.save()
                        break
                else:
                    raise RepositoryError('The physical filesystem does not match with the Directory entry. (Path: %s)' % self.real_path)
            else:
                raise RepositoryError('The new repository directory is missin! (Tried: %s)' % new_repos_path)
        return self.real_path

    class Meta:
        unique_together = (('domain', 'parent', 'name'), )

class File(models.Model):
    belongs_to = models.ForeignKey(Directory)
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(default=datetime.now)
    owner = models.ForeignKey('auth.User')
    team = models.ForeignKey('labsite.Team', blank=True, null=True)
    description = models.CharField(max_length=200)
    size = models.PositiveIntegerField()
    metadata = JSONField(blank=True, null=True)

    def get_real_path(self):
        return self.belongs_to.get_real_path() + (u'/%d' % self.id)

    def __unicode__(self):
        return u'%s @ %s' % (self.name, self.get_real_path())

    class Meta:
        unique_together = (('belongs_to', 'name'), )

class UploadTempFile(models.Model):
    """A light-weight upload tracker model for maintenance."""
    key = models.CharField(max_length=64, db_index=True)
    original_name = models.CharField(max_length=255)
    saved_path = models.CharField(max_length=512)
    started_at = models.DateTimeField(default=datetime.now)

    def __unicode__(self):
        return u'%s (%s @ %s)' % (self.key, self.original_name, self.saved_path)


def get_or_create_directory(domain, path, type, description=u''):
    """
    Creates a repository directory.
    
    This function accepts also recursive definition of path, and
    make the intermediate directories if they're needed.
    In this case, description is applied on the leaf directory only.

    If the given directory already exists, just return it without
    any exception raised.
    """
    parts = path.split(PATHSEP)
    dir_ids = []
    parent = None
    for part in parts:
        if len(part) == 0:
            continue
        try:
            dir = Directory.objects.get(domain=domain, name=part, parent=parent)
            dir_ids.append(dir.id)
            parent = dir
        except Directory.DoesNotExist:
            dir = Directory()
            dir.domain = domain
            dir.name = part
            dir.type = type
            dir.description = description
            dir.parent = parent
            dir.save()
            if parent is None:
                dir.real_path = os.path.join(settings.REPOSITORY_STORAGE_PATH, domain, *map(lambda x: unicode(x), dir_ids + [dir.id]))
            else:
                dir.real_path = os.path.join(parent.real_path, unicode(dir.id))
            dir.save()
            dir_ids.append(dir.id)
            parent = dir
    target_path = os.path.join(settings.REPOSITORY_STORAGE_PATH, domain, *map(lambda x: unicode(x), dir_ids))
    if not os.path.exists(target_path):
        # Ignore already existing leaf directory.
        os.makedirs(target_path)
    return dir

def delete_directory(dir):
    """
    Deletes a repository directory.

    Operates like os.removedirs() function by deleteing empty parent
    directories recursivly also.
    """
    target_path = dir.get_real_path()
    count = 0
    while True:
        if dir.directory_set.count() > 0 or dir.file_set.count() > 0:
            if count == 0:
                raise RepositoryError('The directory is not empty.')
            else:
                break
        dir.delete()
        count += 1
        dir = dir.parent
        if dir is None:
            break
    os.removedirs(target_path)

def delete_file(file):
    try:
        os.remove(file.get_real_path())
    except OSError, detail:
        print>>sys.stderr, u'Deleting file "%s" has failed. %s' % (file.get_real_path(), detail)
    file.delete()
