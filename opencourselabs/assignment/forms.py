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


from django import forms
from opencourselabs.utils.forms import DatePickerWidget, CheckboxListWidget, MultiFileField 
from .models import ASSIGNMENT_TYPES

class CreateForm(forms.Form):
    name = forms.CharField(max_length=120)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows':10, 'cols':75}))
    type = forms.ChoiceField(choices=ASSIGNMENT_TYPES, help_text=u'This cannot be changed afterwards.')
    due_date = forms.DateField(widget=DatePickerWidget())
    due_time = forms.TimeField(initial=u'23:59:59')
    attachments = MultiFileField(required=False)

class ModifyForm(forms.Form):
    name = forms.CharField(max_length=120)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows':10, 'cols':75}))
    due_date = forms.DateField(widget=DatePickerWidget())
    due_time = forms.TimeField(initial=u'23:59:59')
    remove_attachments = forms.BooleanField(required=False, help_text=u'Check this to remove existing attachments. Otherwise, new attachments will be added after existing ones.')
    attachments = MultiFileField(required=False)

class SubmitForm(forms.Form):
    description = forms.CharField(widget=forms.Textarea(attrs={'rows':10, 'cols':75}))
    add_metadata = forms.BooleanField(required=False)
    attachments = MultiFileField(help_text=u'You may upload only one file. If you upload again, the previous one is replaced.')

class MetadataForm(forms.Form):
    """A form for sharing submissions with Hadoop source website."""

    type = forms.ChoiceField(choices=(
        ('EXECUTABLE', u'Executable'),
        ('COMPLEX', u'Complex'),
        ('MAPPER', u'Mapper'),
        ('REDUCER', u'Reducer'),
        ('INPUT', u'InputFormat'),
        ('OUTPUT', u'OutputFormat'),
        ('TYPE', u'Data Type'),
        ('ETC', u'Other'),
    ))
    license = forms.ChoiceField(choices=(
        ('Apache', u'Apache'),
        ('MIT', u'MIT'),
        ('LGPL', u'LGPL'),
        ('GPL', u'GPL'),
        ('Other', u'Other'),
    ))
    license_custom = forms.CharField(max_length=50, required=False, label=u'Custom License')
    hadoop_version = forms.MultipleChoiceField(choices=(
        ('0.20.x', u'0.20.x'),
        ('0.19.x', u'0.19.x'),
        ('0.18.x', u'0.18.x'),
        ('0.17.x', u'0.17.x'),
    ), widget=CheckboxListWidget(attrs={'style':'height:200px'}), label=u'Supported Hadoop Ver.')
    main_class = forms.CharField(max_length=120)

class ResubmitForm(forms.Form):
    description = forms.CharField(widget=forms.Textarea(attrs={'rows':10, 'cols':75}))
    add_metadata = forms.BooleanField(required=False)
    remove_attachments = forms.BooleanField(required=False, help_text=u'Check this to remove existing attachments. Otherwise, new attachments will be added after existing ones.')
    attachments = MultiFileField(label=u'New attachments', required=False)
