# coding=utf-8
"""

Created on 2014-04-03

@author: André Baillargeon
  
"""
import os
import socket
import random
import string
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import mail_admins
from django.core.cache import cache
from heartbeat.models import HeartbeatCache


class Check(object):
    """
    Base Class that needs to be subclassed by a service checker
    """
    def __init__(self, **params):
        self.msg = ''
        self.actions = params.get('actions', {})

    def get_node(self):
        site = Site.objects.get(pk=getattr(settings, 'SITE_ID', 0))
        try:
            hostname = socket.gethostname()
        except:
            hostname = 'Unnamed'
        return site, hostname

    def perform_check(self):
        raise NotImplementedError('You must subbclass Check with the service you want to monitor')


class Flag(Check):
    """
    Check if filename exists and contains 0.
    @returns bool
    """
    def __init__(self, **params):
        super(Flag, self).__init__(**params)
        self.filename = params.get('filename')

    def perform_check(self):
        if self.filename and os.path.exists(self.filename) and '0' in open(self.filename).read():
            self.msg = 'Fail: %s exists and contains 0' % self.filename
            if self.actions.get('mail_admins'):
                mail_admins(u'Flag is present and contains 0', u'%s on host %s is flagged as down' % self.get_node())
            return False if self.actions.get('takedown') else True
        self.msg = 'Ok'
        return True


class Db(Check):
    """
    Check if we can insert a value and retrieve it from db
    @returns bool
    """
    def __init__(self, **params):
        super(Db, self).__init__(**params)
        self.randomval = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))

    def perform_check(self):
        try:
            HeartbeatCache(cache=self.randomval).save()
            heartbeat = HeartbeatCache.objects.get(cache=self.randomval)
            heartbeat.delete()
            self.msg = 'Ok'
            return True
        except Exception as e:
            self.msg = 'Fail: %s' % e
            if self.actions.get('mail_admins'):
                mail_admins(u'Db test failed', u'%s on host %s cannot talk to the db' % self.get_node())
            return False if self.actions.get('takedown') else True


class Cache(Check):
    """
    Check if we can insert a value and retrieve it from cache
    @returns bool
    """
    def __init__(self, **params):
        super(Cache, self).__init__(**params)
        self.randomval = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))

    def perform_check(self):
        cache.set('HEARTBEAT_TEST', self.randomval, 2)
        if not cache.get('HEARTBEAT_TEST', 2) == self.randomval:
            self.msg = 'Fail'
            if self.actions.get('mail_admins'):
                mail_admins(u'Cache test failed', u'%s on host %s cannot talk to the cache' % self.get_node())
            return False if self.actions.get('takedown') else True
        self.msg = 'Ok'
        return True