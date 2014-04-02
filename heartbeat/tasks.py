# coding=utf-8
"""

Created on 2014-04-01

@author: André Baillargeon
  
"""

from celery.task import Task


class TestTask(Task):
    def run(self, x, y):
        print x+y
        return x+y