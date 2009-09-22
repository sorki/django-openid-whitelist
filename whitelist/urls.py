from django.conf.urls.defaults import *

urlpatterns = patterns('whitelist.views',
    url(r'^start$', 'start', name='whitelist-start'),
    url(r'^finish$', 'finish', name='whitelist-finish'),
    url(r'^check$', 'check', name='whitelist-check'),
    url(r'^check_json$', 'check', { 'json' : True }, name='whitelist-check-json'),
)
