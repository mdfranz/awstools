#!/usr/bin/env python

# Set these
#AWS_ACCESS_KEY_ID = ''
#AWS_SECRET_ACCESS_KEY = ''
#AWS_SSH_PEM=''

settings = {}
settings["debug"] = True
settings["sanitize"] = True

import boto,time,sys,os,tempfile

def quotify(s):
    return '"'+s+'"'

def to_dot(sg_list):
    pairs = []
    flows = {}
    for s in sg_list:
        for r in s.rules:
            for g in r.grants:
                if settings['sanitize']:
                    if g.__repr__().find('-') > -1:
                        src = g.__repr__().split('-')[0]
                    else:
                        src = g.__repr__()

                p = (src, s.name)
                if p[0]:
                    if p not in pairs:
                        pairs.append(p)
                        flows[p] = []
                    flows[p].append(r.ip_protocol + "/" + r.to_port)

    for f in flows.keys():
        rules =  " ".join(flows[f])
        label =  '[label="' + rules + '"];'
        print quotify(f[0]) + "->" + quotify(f[1]) + label

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
    else:
        if sys.argv[1] == "plot":
            to_dot(e.get_all_security_groups())
