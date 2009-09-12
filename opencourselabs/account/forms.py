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
from opencourselabs.labsite.models import ORGANIZATIONS

class LoginForm(forms.Form):
    email = forms.CharField(label=u'Email', max_length=30)
    password = forms.CharField(label=u'Password', max_length=60, widget=forms.PasswordInput())

class CreateForm(forms.Form):
    real_name = forms.CharField(label=u'Real Name', min_length=3, max_length=30)
    email = forms.EmailField(label=u'Email', help_text=u'You should enter a valid email. A verification message will be sent.')
    organization = forms.ChoiceField(label=u'Organization', choices=ORGANIZATIONS)
    password = forms.CharField(label=u'Password', widget=forms.PasswordInput())

    def clean_real_name(self):
        real_name = self.cleaned_data['real_name']
        forbidden_names = (
            u'admin', u'administrator', u'kaist', u'snu', u'sysop',
            u'nexr', u'root', u'test', u'system', u'system operator',
            u'관리자', u'운영자', u'시삽',
        )
        if real_name.lower() in forbidden_names:
            raise forms.ValidationError(u'This name is not allowed.')
        return real_name
