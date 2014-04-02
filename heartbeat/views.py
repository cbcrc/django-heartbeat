import os
import string
import random
import json
import pysolr

from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.generic.detail import BaseDetailView
from django.core.cache import cache
from django.conf import settings

from heartbeat.models import HeartbeatCache
from heartbeat.tasks import TestTask

randomval = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))


class JsonResponseMixin(object):

    def render_to_response(self, context, **kwargs):
        return self.get_json_response(self.convert_to_json(context), **kwargs)

    def get_json_response(self, content, **kwargs):
        return HttpResponse(content, content_type='application/json', **kwargs)

    def convert_to_json(self, context):
        return json.dumps(context, indent=4)


class Status(JsonResponseMixin, BaseDetailView):

    def __init__(self):
        self.results = {}
        super(Status, self).__init__()

    def check_flag(self, **params):
        """
        Check services: flag
        """
        takedown = params.get('takedown', False)
        filename = params.get('filename', '')
        if filename and os.path.exists(filename) and '0' in open(filename).read():
            self.results['flag'] = 'Down'
            return False if takedown else True
        self.results['flag'] = 'Ok'
        return True

    def check_database(self, **params):
        """
        Check services: database
        """
        takedown = params.get('takedown', False)
        try:
            HeartbeatCache(cache=randomval).save()
            heartbeat = HeartbeatCache.objects.get(cache=randomval)
            heartbeat.delete()
            self.results['database'] = 'Ok'
            return True
        except Exception as e:
            self.results['database'] = 'Down -- %s' % e
            return False if takedown else True

    def check_cache(self, **params):
        """
        Check services: cache
        """
        takedown = params.get('takedown', False)
        cache.set('HEARTBEAT_TEST', randomval, 2)
        if not cache.get('HEARTBEAT_TEST', 2) == randomval:
            self.results['cache'] = 'Down'
            return False if takedown else True
        self.results['cache'] = 'Ok'
        return True

    def check_rabbitmq(self, **params):
        """
        Check services: rabbitmq
        """
        takedown = params.get('takedown', False)
        try:
            t = TestTask().delay()
            print t.id
            self.results['rabbitmq'] = 'Ok'
            return True
        except Exception as e:
            self.results['rabbitmq'] = 'Down -- %s' % e
            return False if takedown else True

    def check_celeryd(self, **params):
        """
        Check services: celeryd
        """
        takedown = params.get('takedown', False)
        try:
            r = TestTask().delay(1, 1).wait()
            if r.successful():
                self.results['celeryd'] = 'Ok'
                return True
        except Exception as e:
            self.results['celeryd'] = 'Down -- %s' % e
            return False if takedown else True

    def check_solr(self, **params):
        """
        Check services: solr
        """
        takedown = params.get('takedown', False)
        url = params.get('url', '')
        try:
            solr = pysolr.Solr(url, timeout=2)
            results = solr.search('*:*')
            if results.hits:
                self.results['solr'] = 'Ok'
                return True
        except Exception as e:
            self.results['solr'] = 'Down -- %s' % e
            return False if takedown else True

    def get_services(self):
        """
        Get all services from settings
        """
        #TODO OrderDict
        return getattr(settings, 'HEARTBEAT', {})

    def _quote(self, val):
        if isinstance(val, str):
            return '"%s"' % val
        return val

    @never_cache
    def dispatch(self, request, *args, **kwargs):
        """
        returns results in json with:
        status 503 if one of the check methods returns False
        status 200 if all of the check methods returns True
        """

        # prepare the results to display
        for service in self.get_services().iterkeys():
            self.results[service] = 'Not tested'

        # call the validation method for each service in settings
        for service, params in self.get_services().iteritems():
            try:
                params = ', '.join(['%s=%s' % (param, self._quote(value)) for param, value in params.iteritems()])
                print service, params
                if not eval('self.check_%s(%s)' % (service, params)):
                    return self.render_to_response(
                        {'services': self.results, 'header': '503, %s failed' % service}, status=503)
            except AttributeError:
                self.results[service] = '%s is not a defined service you can check.' % service
                continue



        return self.render_to_response({'services': self.results, 'header': '200' })