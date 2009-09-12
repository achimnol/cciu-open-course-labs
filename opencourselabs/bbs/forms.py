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
from opencourselabs.utils.forms import MultiFileField
from .models import Article

class WriteForm(forms.ModelForm):
    attachments = MultiFileField(required=False)

    class Meta:
        model = Article
        exclude = ('belongs_to', 'author', 'written_at', 'modified_at', 'is_notice', 'tags')

class StaffWriteForm(forms.ModelForm):
    attachments = MultiFileField(required=False)

    class Meta:
        model = Article
        exclude = ('belongs_to', 'author', 'written_at', 'modified_at', 'tags')

class CommentForm(forms.Form):
    content = forms.CharField(max_length=500)
