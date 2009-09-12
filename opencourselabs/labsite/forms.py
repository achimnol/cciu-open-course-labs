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


import re
from django import forms
from opencourselabs.labsite.models import NewRequest, Team, ORGANIZATIONS
from opencourselabs.utils.forms import DatePickerWidget, CheckboxListWidget

class BrowseForm(forms.Form):
    OPTIONAL_ORGANIZATIONS = (
        (u'all', u'All'),
    ) + ORGANIZATIONS
    STATUSES = (
        (u'all', u'All'),
        (u'active', u'Active'),
        (u'inactive', u'Inactive'),
    )
    organization = forms.TypedChoiceField(choices=OPTIONAL_ORGANIZATIONS, empty_value=u'all', required=False)
    course = forms.CharField(required=False)
    status = forms.ChoiceField(choices=STATUSES, required=False, initial=u'active')

class RequestForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={'rows':8, 'cols':60}))
    period_begin = forms.DateField(widget=DatePickerWidget(), label=u'Start of usage period')
    period_end = forms.DateField(widget=DatePickerWidget(), label=u'End of usage period',
        help_text=u'Note that the contents will be archived after this date unless you explicitly delete them.<br/>But you won\'t be able to use our resources from then.')

    def clean_contact_cellphone(self):
        value = self.cleaned_data['contact_cellphone']
        # TODO: should we consider other countrys' phone code rules?
        if re.match(ur'^0\d\d?-\d{3,4}-\d{3,4}$', value) is None:
            raise forms.ValidationError(u'Invalid cellphone number format.')
        return value

    def clean_cloud(self):
        value = self.cleaned_data['cloud']
        if value != 'nexr-vc3':
            raise forms.ValidationError(u'Only NexR iCube is supported currently.')
        return value

    class Meta:
        model = NewRequest
        exclude = ['creator', 'status', 'created_at', 'approved_at']
    
class RequestApprovalForm(forms.Form):
    num_vm = forms.IntegerField(label=u'Number of VMs')
    num_ip = forms.IntegerField(label=u'Number of IPs')

class JoinRequestApprovalForm(forms.Form):
    request_id = forms.IntegerField()
    type = forms.ChoiceField(choices=(('staff', u'Staff'), ('student', u'Student')))

class UserMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, instance):
        return u'%s (%s)' % (instance.get_profile().real_name, instance.email)

class CreateTeamForm(forms.ModelForm):
    members = UserMultipleChoiceField('auth.User',
        widget=CheckboxListWidget,
    )

    class Meta:
        model = Team
        exclude = ['belongs_to',]

class ModifyTeamForm(forms.ModelForm):
    members = UserMultipleChoiceField('auth.User',
        widget=CheckboxListWidget,
    )
    
    class Meta:
        model = Team
        exclude = ['belongs_to', 'num_vm', 'use_hadoop']

class AddInstancesForm(forms.Form):
    redeploy_hadoop = forms.BooleanField(label=u'(Re)deploy Hadoop', required=False)
    num_instances = forms.IntegerField(label=u'Num. Instances to Add', min_value=0, widget=forms.TextInput(attrs={'style':'width:5em'}))

class SettingsForm(forms.Form):
    title = forms.CharField(max_length=60)
    question1 = forms.CharField(max_length=200, required=False)
    question2 = forms.CharField(max_length=200, required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows':10, 'cols':70}))
