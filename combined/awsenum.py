#!/usr/bin/env python

# Developed against Python Boto v 2.9.8

from socket import gethostbyaddr
from optparse import OptionParser
from boto.s3.connection import S3Connection
from boto.ec2.elb import ELBConnection
from boto.ec2 import EC2Connection

class instance_enum():
    def __init__(self,c,resolve_hosts=False):
        self.c=c
        self.resolve_hosts = resolve_hosts
        self.addrs = c.get_all_addresses()

    def get_hosts(self):
        hosts = []
        for a in self.addrs:
            if a.instance_id:
                hosts.append(a.public_ip)
        return hosts
            
class elb_enum():
    def __init__(self,c,resolve_hosts=False):
       self.c=c
       self.lbs = c.get_all_load_balancers()
       self.resolve_hosts = resolve_hosts

    def get_hosts(self):
        hosts = []
        for lb in self.lbs:
            if not self.resolve_hosts:
                try:
                    hosts.append(gethostbyaddr(lb.dns_name)[2][0])
                except:
                    pass
            else:
                hosts.append(lb.dns_name)
        return hosts

    def get_urls(self):
        pass

class s3_enum():
    def __init__(self,c):
        self.c = c
        self.server = c.host

    def get_urls(self):
        urls = []
        for b in self.c.get_all_buckets():
            for f in b.get_all_keys():
                url = "%s://%s/%s/%s" % ('http',self.server,b.name,f.name)
                urls.append(url.rstrip())
        return urls

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i","--ip",action="store_true",dest="ip",default=True, help="Dump L3 addresses")
    parser.add_option("-v","--verbose",action="store_true",dest="verbose",default=True, help="Verbose output")
    parser.add_option("-u","--url",action="store_true",dest="url",default=False,help="Dump URLs")
    parser.add_option("-s","--sql",action="store_true",dest="sql",default=False,help="Dump Database Connection")
    parser.add_option("-n","--noresolv",action="store_true",dest="noresolv",default=True,help="Do not perform DNS resolution")

    (options,args) = parser.parse_args()

    hosts = []
    urls = []

    if options.ip:
        elb = elb_enum(ELBConnection())
        ec2 = instance_enum(EC2Connection())

        all_hosts = [ elb.get_hosts() , ec2.get_hosts() ]

        for src in all_hosts:
            for h in src:
                if h not in hosts:
                    hosts.append(h)
        for h in sorted(hosts):
            print h
    if options.url:
        s3 = s3_enum(S3Connection)
        all_urls = [ s3_enum.get_hosts() ]

        for src in all_urls:
            for h in src:
                if u not in urls:
                    urls.append(u)

        for h in sorted(urls):
            print u

