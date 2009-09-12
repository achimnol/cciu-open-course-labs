from django.conf.urls.defaults import *

urlpatterns = patterns('opencourselabs.assignment.views',
    url(ur'^create/$', 'create', name='assignment-create'),
    url(ur'^modify/$', 'modify', name='assignment-modify'),
    url(ur'^list/$', 'list', name='assignment-list'),
    url(ur'^detail/$', 'detail', name='assignment-detail'),
    url(ur'^detail/download/.*$', 'download', name='assignment-download'),
    url(ur'^submission/detail/$', 'submission_detail', name='assignment-submission-detail'),
    # See the comments at views.submission_download for ".*".
    url(ur'^submission/download/.*$', 'submission_download', name='assignment-submission-download'),
    url(ur'^modify/$', 'modify', name='assignment-modify'),
    url(ur'^submit/$', 'submit', name='assignment-submit'),
)
