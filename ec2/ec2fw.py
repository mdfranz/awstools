#!/usr/bin/env python

# Set these
#AWS_ACCESS_KEY_ID = ''
#AWS_SECRET_ACCESS_KEY = ''
#AWS_SSH_PEM=''

import boto,time,sys,os,tempfile

def show_sg(e):
    """Dump out all the instances per reservation"""
    print "---- Security Groups ----"
    for s in e.get_all_security_groups():
        print "[%s]" % s.name
        for i in s.instances():
            print " - " +  i.public_dns_name

if __name__ == "__main__":
    print "Connecting to EC2..."
    e = boto.connect_ec2()
    if len(sys.argv) == 1:
        show_sg(e)
        sys.exit()
