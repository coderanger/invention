from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.simple import redirect_to

import invention.views

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', invention.views.index, name='index'),
    url(r'^(\d+)/(?:(.*)/)?$', invention.views.invention, name='invention'),
    url(r'^_autocomplete/$', invention.views.autocomplete),
    url(r'^_items/$', invention.views.items),
    url(r'^search/$', invention.views.search),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^favicon.ico$', redirect_to, {'url': settings.STATIC_URL+'favicon.ico'}),
)
