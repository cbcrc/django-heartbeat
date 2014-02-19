import os
import string
import random

from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.core.cache import cache
from django.conf import settings

from heartbeat.models import HeartbeatCache

@never_cache
def status(request, *args, **kwargs):
    # check the file flag
    if getattr(settings, 'HEARTBEAT_FILENAME', False) and \
        os.path.exists(settings.HEARTBEAT_FILENAME) and \
            '0' in open(settings.HEARTBEAT_FILENAME).read():
        return HttpResponse('Server maintenance under way', status=503)
    
    # check for caching
    val = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    cache.set('HEARTBEAT_TEST', val, 2)
    if not cache.get('HEARTBEAT_TEST', 2) == val:
        return HttpResponse('Server cache is down', status=503)

    # check for db
    try:
        HeartbeatCache(cache=val).save()
        heartbeat = HeartbeatCache.objects.get(cache=val)
        heartbeat.delete()
    except Exception as e:
        return HttpResponse('Server db is down: %s' % e, status=503)

    # all good
    return HttpResponse('OK')