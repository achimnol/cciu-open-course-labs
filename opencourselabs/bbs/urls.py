from django.conf.urls.defaults import *

urlpatterns = patterns('opencourselabs.bbs.views',
    url(ur'^$', 'index'),
    url(ur'^(?P<board_id>\d+)/$', 'list', name='bbs-list'),
    url(ur'^(?P<board_id>\d+)/view/(?P<article_id>\d+)/$', 'view', name='bbs-view'),
    url(ur'^(?P<board_id>\d+)/write/$', 'write', kwargs={'mode':'create'}, name='bbs-write'),
    url(ur'^(?P<board_id>\d+)/attachment/.*$', 'download_attachment', name='bbs-attachment-download'),
    url(ur'^(?P<board_id>\d+)/modify/$', 'write', kwargs={'mode':'modify'}, name='bbs-modify'),
    url(ur'^(?P<board_id>\d+)/delete/$', 'delete', name='bbs-delete'),
    url(ur'^(?P<board_id>\d+)/comment/$', 'comment', name='bbs-comment'),
)
