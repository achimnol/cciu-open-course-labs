#! /usr/bin/env python
import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'opencourselabs.settings'

from django.core.handlers import wsgi 
application = wsgi.WSGIHandler()

# vim: set ft=python:
