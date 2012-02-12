#!/usr/bin/env python

# Set these
#AWS_ACCESS_KEY_ID = ''
#AWS_SECRET_ACCESS_KEY = ''
#AWS_SSH_PEM=''

settings = {}
settings["debug"] = True

import boto,time,sys,os,tempfile

def show_sg(e):
    """Dump out all the instances per reservation"""
    for s in e.get_all_security_groups():
        print "\n --- %s/%s ---" % (s.name,s.id)
        print "[Instance Members]"
        for i in s.instances():
            print "\t%s (%s)" % (i.public_dns_name, i.private_ip_address)
        print "[Rules]"
        for r in s.rules:
            print "\t SRC: %s DST: %s/%s " % (r.grants,r.ip_protocol,r.to_port)

if __name__ == "__main__":
    if settings["debug"]:
        print "Connecting to EC2..."
    e = boto.connect_ec2()

    if len(sys.argv) == 1:
        show_sg(e)
        sys.exit()
