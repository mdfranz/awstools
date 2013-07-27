#!/usr/bin/env python

from awsenum import *

class target_db():
    def __init__(self,target):
        self.target = target
        # {'host': 'localhost', 'type': 'mongodb'}
        self.connection = None

    def connect(self):
        if self.connection['type'] == "mongodb":
            import pymongo

    def has_instance(self,instance_id)
        """Check if an instance is in the database"""
        pass

    def has_host(self,h):
        """Check if a host is in the database""" 
        pass

    def has_url(self,u):
        """Check if URL is in the database"""

    def host_has_port(self,h,p):
        """Check if a given Host has a listening port"""
        pass
