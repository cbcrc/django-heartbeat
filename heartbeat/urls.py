from django.conf.urls import patterns, url
from heartbeat.views import Status

urlpatterns = patterns('heartbeat.views',
                       url(r'^status/$', Status.as_view(), name='status'))