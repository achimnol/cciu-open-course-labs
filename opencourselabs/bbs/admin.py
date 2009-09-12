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


from django.contrib import admin
from .models import Board, Article, Comment, Tag

class BoardAdmin(admin.ModelAdmin):
    list_display = ('title', 'belongs_to', 'owner')

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'belongs_to', 'author', 'written_at', 'modified_at')
    list_filter = ('belongs_to', )
    ordering = ('-written_at', )

class CommentAdmin(admin.ModelAdmin):
    list_display = ('belongs_to', 'author', 'body', 'written_at')
    ordering = ('-written_at', )

admin.site.register(Board, BoardAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Tag)
