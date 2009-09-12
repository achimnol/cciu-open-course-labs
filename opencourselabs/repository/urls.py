from django.conf.urls.defaults import *

urlpatterns = patterns('opencourselabs.repository.views',
    url('^$', 'index'),
)
