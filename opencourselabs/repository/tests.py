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


import os, os.path
from django.conf import settings
from django.db import models
from django.test import TestCase
from .models import Directory, File
from .models import get_or_create_directory, delete_directory
from .fields import PickledObjectField

class TestingModel(models.Model):
    pickle_field = PickledObjectField()

class TestCustomDataType(str):
    pass

class PickledObjectFieldTests(TestCase):
    def setUp(self):
        self.testing_data = (
            {1:1, 2:4, 'asdf\xff':6, u'EscapeTest:\\\'':8, 5:u'와우'},
            u'안녕 세상!',
            (1, 2, 3, 4, 5),
            [1, 2, 3, 4, 5],
            TestCustomDataType('Hello World'),
        )
        return super(PickledObjectFieldTests, self).setUp()
    
    def testDataIntegriry(self):
        """Tests that data remains the same when saved to and fetched from the database."""
        for value in self.testing_data:
            model_test = TestingModel(pickle_field=value)
            model_test.save()
            model_test = TestingModel.objects.get(id__exact=model_test.id)
            self.assertEquals(value, model_test.pickle_field)
            model_test.delete()
    
    def testLookups(self):
        """Tests that lookups can be performed on data once stored in the database."""
        for value in self.testing_data:
            model_test = TestingModel(pickle_field=value)
            model_test.save()
            self.assertEquals(value, TestingModel.objects.get(pickle_field__exact=value).pickle_field)
            model_test.delete()

class ModelTest(TestCase):
    def test_get_or_create_directory(self):
        dir = get_or_create_directory('test', u'한글', 0)
        expected_path = os.path.join(settings.REPOSITORY_STORAGE_PATH, 'test', unicode(dir.id))
        self.assertEquals(1, Directory.objects.count())
        self.assertEquals(expected_path, dir.get_real_path())
        self.assertTrue(os.path.exists(expected_path))

        Directory.objects.all().delete()
        os.removedirs(expected_path)

        # Check if it correctly creates intermediate directories recursively.
        dir = get_or_create_directory('test', u'a/b/c', 0)
        expected_path1 = os.path.join(settings.REPOSITORY_STORAGE_PATH, 'test', *map(lambda x: unicode(x), [dir.parent.parent.id, dir.parent.id, dir.id]))
        self.assertEquals(3, Directory.objects.count())
        self.assertEquals(expected_path1, dir.get_real_path())
        self.failUnless(os.path.exists(expected_path1))
        old_id = dir.id
        parent_id = dir.parent.id

        # Check if things goes well when we try to create existing directories.
        dir = get_or_create_directory('test', u'a/b/c', 0)
        self.assertEquals(3, Directory.objects.count())
        self.assertEquals(old_id, dir.id)
        dir = get_or_create_directory('test', u'a/b/', 0)
        self.assertEquals(3, Directory.objects.count())
        self.assertEquals(parent_id, dir.id)

        # Check if it goes smoothly with already existing intermediate directories.
        dir = get_or_create_directory('test', u'a/b/d', 0)
        expected_path2 = os.path.join(settings.REPOSITORY_STORAGE_PATH, 'test', *map(lambda x: unicode(x), [dir.parent.parent.id, dir.parent.id, dir.id]))
        self.assertEquals(4, Directory.objects.count())
        self.assertEquals(expected_path2, dir.get_real_path())
        self.failUnless(os.path.exists(expected_path2))
        self.failUnless(dir.parent.id == parent_id)

        Directory.objects.all().delete()
        os.removedirs(expected_path1)
        os.removedirs(expected_path2)

    def test_delete_directory(self):
        dir1 = get_or_create_directory('test', u'와우', 0)
        real_path1 = os.path.join(settings.REPOSITORY_STORAGE_PATH, 'test', unicode(dir1.id))
        dir2 = get_or_create_directory('test', u'a/b/c', 0)
        real_path2 = os.path.join(settings.REPOSITORY_STORAGE_PATH, 'test', *map(lambda x: unicode(x), [dir2.parent.parent.id, dir2.parent.id, dir2.id]))
        dir3 = get_or_create_directory('test', u'a/b/d', 0)
        real_path3 = os.path.join(settings.REPOSITORY_STORAGE_PATH, 'test', *map(lambda x: unicode(x), [dir3.parent.parent.id, dir3.parent.id, dir3.id]))

        delete_directory(dir1)
        self.assertEquals(4, Directory.objects.count())
        self.failIf(os.path.exists(real_path1))

        delete_directory(dir2)
        self.assertEquals(3, Directory.objects.count())
        self.failIf(os.path.exists(real_path2))

        delete_directory(dir3)
        self.assertEquals(0, Directory.objects.count())

