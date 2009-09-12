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


import os, shutil
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import F, Q, Count
from django.forms import model_to_dict
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic.list_detail import object_list
from opencourselabs.labsite.decorators import labsite_context, team_context, labsite_perm_required
from opencourselabs.repository.models import File, Directory, get_or_create_directory, delete_directory, delete_file, DIRECTORY_TYPES
from opencourselabs.utils import respond_as_attachment
from opencourselabs.utils.decorators import persistent_params
from .forms import WriteForm, StaffWriteForm, CommentForm
from .models import Board, Article, Comment, Tag


@login_required
@labsite_perm_required('staff', 'student')
@team_context
def index(request, labsite, user_team):
    board = get_object_or_404(Board, belongs_to=labsite, title=u'default')
    page = request.GET.get('page', 1)
    return object_list(request,
        Article.objects.filter(belongs_to=board).annotate(comment_count=Count('comment')).select_related(depth=1),
        paginate_by=15,
        page=page,
        template_name='bbs/list.html',
        template_object_name='article',
        extra_context={
            'board': board,
            'labsite': labsite,
            'user_team': user_team,
        },
    )

@login_required
@labsite_perm_required('staff', 'student')
@team_context
def list(request, labsite, user_team, board_id):
    board = get_object_or_404(Board, id=board_id)
    page = request.GET.get('page', 1)
    return object_list(request,
        Article.objects.filter(belongs_to=board).annotate(comment_count=Count('comment')).select_related(depth=1),
        paginate_by=15,
        page=page,
        template_name='bbs/list.html',
        template_object_name='article',
        extra_context={
            'board': board,
            'labsite': labsite,
            'user_team': user_team,
        },
    )

@login_required
@persistent_params('page')
@labsite_perm_required('staff', 'student')
@team_context
def write(request, labsite, user_team, board_id, mode='create'):
    err_msg = u''
    board = get_object_or_404(Board, id=board_id)
    article = None
    if request.method == 'POST':
        if request.user.has_row_perm(labsite, 'staff'):
            if mode == 'create':
                f = StaffWriteForm(request.POST)
            else:
                f = StaffWriteForm(request.POST, instance=get_object_or_404(Article, id=request.GET.get('id', None)))
        else:
            if mode == 'create':
                f = WriteForm(request.POST)
            else:
                f = WriteForm(request.POST, instance=get_object_or_404(Article, id=request.GET.get('id', None)))
        if f.is_valid():
            article = f.save(commit=False)
            article.belongs_to = board
            article.author = request.user
            article.save()
            remove_attachments = bool(request.POST.get('remove_attachments', False))
            if remove_attachments:
                if article.attachments.count() > 0:
                    dir = article.attachments.all()[0].belongs_to
                    for file in article.attachments.all():
                        delete_file(file)
                    if len(f.cleaned_data['attachments']) == 0:
                        delete_directory(dir)
            if len(f.cleaned_data['attachments']) > 0:
                dir = get_or_create_directory(
                    labsite.url_key, u'%s/%s' % (board.id, article.id),
                    DIRECTORY_TYPES.PUBLIC,
                    u'BBS Attachments'
                )
                for temp_file in f.cleaned_data['attachments']:
                    file = dir.file_set.create(
                        name=temp_file.original_name,
                        owner=request.user,
                        team=None,
                        description=u'',
                        size=os.stat(temp_file.saved_path).st_size,
                    )
                    article.attachments.add(file)
                    shutil.move(temp_file.saved_path, file.get_real_path())
                    temp_file.delete()
            return HttpResponseRedirect(reverse('labsite:bbs-view', kwargs={
                'url_key': labsite.url_key,
                'board_id': board.id,
                'article_id': article.id
            }))
        else:
            err_msg = u'Please check your input.'
    else:
        if mode == 'modify':
            article = get_object_or_404(Article, id=request.GET.get('id', None))
        if request.user.has_row_perm(labsite, 'staff'):
            if mode == 'create':
                f = StaffWriteForm()
            else:
                f = StaffWriteForm(initial=model_to_dict(article))
        else:
            if mode == 'create':
                f = WriteForm()
            else:
                f = WriteForm(initial=model_to_dict(article))
    return render_to_response('bbs/write.html', {
        'article': article,
        'write_form': f,
        'board': board,
        'labsite': labsite,
        'user_team': user_team,
        'mode': mode,
        'page': request.GET.get('page', 1),
    }, context_instance=RequestContext(request))

@login_required
@persistent_params('page')
@labsite_perm_required('staff', 'student')
@team_context
def delete(request, labsite, user_team, board_id):
    board = get_object_or_404(Board, id=board_id)
    article = get_object_or_404(Article, id=request.GET.get('id', None))
    if article.author == request.user or request.user.has_row_perm(labsite, 'staff'):
        for file in article.attachments.all():
            delete_file(file)
        article.delete()
    else:
        raise PermissionDenied()
    return HttpResponseRedirect(reverse('labsite:bbs-list', args=(labsite.url_key, board.id)))

@login_required
@persistent_params('page')
@labsite_perm_required('staff', 'student')
@team_context
def view(request, labsite, user_team, board_id, article_id):
    board = get_object_or_404(Board, id=board_id)
    article = get_object_or_404(Article, id=article_id)
    return render_to_response('bbs/view.html', {
        'board': board,
        'article': article,
        'labsite': labsite,
        'user_team': user_team,
        'page': request.GET.get('page', None),
    }, context_instance=RequestContext(request))

@login_required
@persistent_params('page')
@labsite_perm_required('staff', 'student')
@team_context
def comment(request, labsite, user_team, board_id):
    action = request.GET.get('action', 'view')
    article_id = request.GET.get('article_id', None)
    board = get_object_or_404(Board, id=board_id)
    article = get_object_or_404(Article, id=article_id)
    if action == 'view':
        pass
    elif action == 'add':
        f = CommentForm(request.POST)
        if f.is_valid():
            comment = Comment()
            comment.belongs_to = article
            comment.author = request.user
            comment.body = f.cleaned_data['content']
            comment.save()
            return HttpResponseRedirect(reverse('labsite:bbs-view', args=(labsite.url_key, board.id, article.id)))
        else:
            return HttpResponseBadRequest()
    elif action == 'delete':
        comment = get_object_or_404(Comment, id=request.GET.get('id', None))
        if request.user != comment.author and not request.user.has_row_perm(labsite, 'staff'):
            raise PermissionDenied()
        comment.delete()
        return HttpResponseRedirect(reverse('labsite:bbs-view', args=(labsite.url_key, board.id, article.id)))
    else:
        return HttpResponseBadRequest('Invalid action')

@login_required
@labsite_perm_required('staff', 'student')
@team_context
def download_attachment(request, labsite, user_team, board_id):
    board = get_object_or_404(Board, id=board_id)
    article = get_object_or_404(Article, id=request.GET.get('article_id'))
    file = get_object_or_404(File, id=request.GET.get('file_id'))
    return respond_as_attachment(request, file.get_real_path(), file.name)
