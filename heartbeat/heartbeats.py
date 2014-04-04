# coding=utf-8
"""

Created on 2014-04-03

@author: André Baillargeon
  
"""
import random
import string
import os
from heartbeat.models import HeartbeatCache
from django.core.cache import cache


class Check(object):
    """
    Base Class that needs to be subclassed by a service checker
    """
    def __init__(self, **params):
        self.msg = ''
        self.actions = params.get('actions', {})

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
            return False if self.actions.get('takedown') else True
        self.msg = 'Ok'
        return True