# Django settings for CCI:U Open Course Labs project.

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


import os.path
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'dev.db'             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.
TEST_DATABASE_CHARSET = 'utf8'
TEST_DATABASE_COLLATION = 'utf8_general_ci'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Asia/Seoul'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media-admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '5cv*6gxjx3a0$is6d)68!pj@ag_50!-g%4kfp@nh(g5qo7=o6r'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#    'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

ROOT_URLCONF = 'opencourselabs.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
)

FIXTURE_DIRS = (
    os.path.join(PROJECT_PATH, 'fixtures'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'django.contrib.admin',
    'opencourselabs.account',
    'opencourselabs.utils',
    'opencourselabs.labsite',
    'opencourselabs.cloud',
    'opencourselabs.bbs',
    'opencourselabs.home',
    'opencourselabs.assignment',
    'opencourselabs.repository',
    'django_extensions',
)
LOGIN_URL = '/login/'
AUTH_PROFILE_MODULE = 'account.userprofile'

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 2*3600

REPOSITORY_STORAGE_PATH = os.path.join(PROJECT_PATH, 'repository/storage')

EC2_REST_URL = ''
EC2_ACCESS_KEY = ''
EC2_SECRET_KEY = ''
EC2_DEFAULT_TYPE = ''
EC2_HADOOP_MASTER_TYPE = ''
EC2_DEFAULT_IMAGE = ''
EC2_DEFAULT_HADOOP_IMAGE = ''
EC2_DEFAULT_SECURITYGROUP = ''

ICUBE_REST_URL = ''
ICUBE_ACCESS_KEY = ''
ICUBE_SECRET_KEY = ''
ICUBE_DEFAULT_TYPE = ''
ICUBE_HADOOP_MASTER_TYPE = ''
ICUBE_DEFAULT_IMAGE = ''
ICUBE_DEFAULT_HADOOP_IMAGE = ''
ICUBE_DEFAULT_SECURITYGROUP = ''

TWISTED_PORT = 8081

try:
    from opencourselabs.settings_local import *
except ImportError:
    pass
