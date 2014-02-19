# coding=utf-8
"""

Created on 2/19/14

@author: monizh
  
"""
from django.db import models


class HeartbeatCache(models.Model):
    cache = models.CharField(max_length=64)