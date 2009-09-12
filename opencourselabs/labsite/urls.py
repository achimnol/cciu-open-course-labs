from django.conf.urls.defaults import *

labsite_urlpatterns = patterns('opencourselabs.labsite.views',
    url(ur'^$', 'dashboard', name='dashboard'),
    url(ur'^join/$', 'new_join_request'),
    url(ur'^members/$', 'list_members', name='members'),
    url(ur'^teams/$', 'list_teams', name='teams'),
    url(ur'^teams/(?P<team_id>[0-9]+)/$', 'view_team_console', name='team-console'),
    url(ur'^manage/instances/$', 'view_labsite_console', name='console'),
    url(ur'^manage/teams/$', 'list_teams', name='manage-teams'),
    url(ur'^manage/teams/create/$', 'create_team'),
    url(ur'^manage/teams/modify/$', 'modify_team'),
    url(ur'^manage/teams/delete/$', 'delete_team'),
    url(ur'^manage/join-requests/$', 'list_join_requests', name='join-requests'),
    url(ur'^manage/join-requests/approve/$', 'approve_join_request'),
    url(ur'^manage/join-requests/deny/$', 'deny_join_request'),
    url(ur'^manage/members/delete/$', 'delete_member'),
    url(ur'^manage/settings/$', 'modify_settings'),
    #url(ur'^repository/', include('opencourselabs.repository.urls')),
    url(ur'^assignment/', include('opencourselabs.assignment.urls')),
    url(ur'^bbs/', include('opencourselabs.bbs.urls')),
)

urlpatterns = patterns('opencourselabs.labsite.views',
    url(ur'^$', 'index', name='index'),
    url(ur'^browse/$', 'browse', name='browse'),
    url(ur'^request/new/$', 'new_request', name='new_request'),
    url(ur'^(?P<url_key>[-a-zA-Z0-9]+)/', include(labsite_urlpatterns)),
)
