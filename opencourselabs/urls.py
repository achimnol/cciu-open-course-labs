from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',

    (ur'^$', 'opencourselabs.home.views.index'),
    (ur'^account/', include('opencourselabs.account.urls')),
    (ur'^lab/', include('opencourselabs.labsite.urls', namespace='labsite')),
    (ur'^login/', 'opencourselabs.account.views.login'),
    (ur'^logout/', 'opencourselabs.account.views.logout'),
	(ur'^repository/temp-uploader/(?P<action>[a-z]+)', 'opencourselabs.repository.views.temp_upload'),
    (ur'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': './media'}),

    # Uncomment the next line to enable the admin:
    (ur'^admin/', include(admin.site.urls)),
)
