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


import os
from django import forms
from django.conf import settings
from django.forms.fields import EMPTY_VALUES
from django.template import Context
from django.template.loader import render_to_string
from django.utils import simplejson as json
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from opencourselabs.repository.models import UploadTempFile

class DatePickerWidget(forms.DateInput):
    class Media:
        js = ('/media/js/jquery-ui-1.7.2.custom.min.js',)
        css = {
            'all': ('/media/css/ui-lightness/jquery-ui-1.7.2.custom.css',),
        }
    
    def render(self, name, value, attrs=None):
        output = super(forms.DateInput, self).render(name, value, attrs)
        output += u'<script type="text/javascript">$(document).ready(function(){ $(\'#%(id)s\').datepicker({dateFormat:\'yy-mm-dd\'}); });</script>' % {'id': attrs['id']} 
        return mark_safe(output)

class CheckboxListWidget(forms.Widget):
    """
    A multiple checkbox list widget.

    Almost same thing is provided by Django, CheckboxSelectMultiple widget,
    but it cannot be customized because it does not provide any class attribute
    for its outer <ul> element.
    """

    def __init__(self, attrs=None, choices=()):
        super(CheckboxListWidget, self).__init__(attrs)
        self.choices = list(choices)

    def render(self, name, value, attrs=None):
        if value is None:
            str_values = []
        else:
            str_values = [force_unicode(v) for v in value]
        checked_choices = []
        for item in self.choices:
            checked_choices.append({
                'value': item[0],
                'display_text': item[1],
                'checked': force_unicode(item[0]) in str_values,
            })
        return mark_safe(render_to_string('widgets/checkboxlist.html', {
            'id': attrs['id'],
            'name': name,
            'choices': checked_choices,
        }))

    def value_from_datadict(self, data, files, name):
        return data.getlist(name)

class MultiFileFlashWidget(forms.Widget):
    """
    A multiple-file uploads widget implemented with SWFUpload.

    The real files will be stored as temporary files (such as /tmp),
    and can be tracked with UploadTempFile records in the database.
    """

    class Media:
        js = ('/media/js/swfupload.js', '/media/js/jquery-swfupload.js', '/media/js/jquery-cookie.js', '/media/js/math.uuid.js')
        css = {
            'all': ('/media/css/ui-upload.css',)
        }

    def render(self, name, value, attrs=None):
        try:
            session_name = settings.SESSION_COOKIE_NAME
        except NameError:
            session_name = 'sessionid'

        return mark_safe(render_to_string('widgets/swfupload.html', {
            'id': attrs['id'],
            'name': name,
            'value': value,
            'session_name': session_name,
            'debug': settings.DEBUG,
        }))

class MultiFileField(forms.Field):
    """
    A multiple file field that receives the files alongside other fields.
    """
    widget = MultiFileFlashWidget

    def __init__(self, strict=False, count=1, *args, **kwargs):
        """
        Arguments:
            strict -- Makes extra validation performed.
            count  -- Specifies the number of files to be uploaded 
        """
        super(MultiFileField, self).__init__(*args, **kwargs)
        self.strict = strict
        self.count = count

    def _delete_temp_files(self):
        files = UploadTempFile.objects.filter(key=data)
        for f in files:
            if os.path.isfile(f.saved_path):
                os.remove(f.saved_path)
        files.delete()

    def clean(self, data):
        super(MultiFileField, self).clean(data)

        if not self.required and data in EMPTY_VALUES:
            return None
        try:
            # The following model is imported only when needed.
            files = UploadTempFile.objects.filter(key=data)
        except UploadTempFile.DoesNotExist:
            raise ValidationError(_(u"No file was submitted."))

        for f in files:
            if not os.path.isfile(f.saved_path) or os.stat(f.saved_path).st_size == 0:
                self._delete_temp_files()
                raise ValidationError(_(u"The submitted file (%(filename)s) is empty.") % {'filename': f.original_name})
        
        # TODO: support this when we implement multiple uploads.
        #if self.strict and len(files) != self.count:
        #    self._delete_temp_files()
        #    raise ValidationError(_(u"An incorrect number of files were uploaded."))
        
        return files
