# coding=utf-8
"""

Created on 2014-04-03

@author: André Baillargeon

"""
import importlib
import json
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.generic.detail import BaseDetailView


class JsonResponseMixin(object):

    def render_to_response(self, context, **kwargs):
        return self.get_json_response(self.convert_to_json(context), **kwargs)

    def get_json_response(self, content, **kwargs):
        return HttpResponse(content, content_type='application/json', **kwargs)

    def convert_to_json(self, context):
        return json.dumps(context, indent=4)


class Status(JsonResponseMixin, BaseDetailView):

    def _quote(self, val):
        if isinstance(val, str):
            return '"%s"' % val
        return val

    def get_services(self):
        """
        Get all services from settings
        """
        return getattr(settings, 'HEARTBEAT', {})

    def load_class(self, full_class_string):
        """
        load load from string
        """
        class_data = full_class_string.split(".")
        module_path = ".".join(class_data[:-1])
        class_str = class_data[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_str)

    @never_cache
    def dispatch(self, request, *args, **kwargs):
        """
        returns results in json with:
        status 503 if one of the perform_check returns False
        status 200 if all of the perform_check returns True
        """
        results = {}
        error = False
        # call the validation method for each service in settings
        for service_name, params in self.get_services().iteritems():
            results[service_name] = 'Not tested'

            # get, import and instanciate module
            klass = params.get('class')
            try:
                service_module = self.load_class(klass)
            except (ImportError, AttributeError) as e:
                results[service_name] = str(e)
                continue
            service = service_module(**params)

            # perform check
            if not service.perform_check():
                error = True
            results[service_name] = service.msg

        if error:
            return self.render_to_response(
                    {'services': results, 'header': '503'}, status=503)
        return self.render_to_response({'services': results, 'header': '200' })