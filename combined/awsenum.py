#!/usr/bin/env python

# Developed against Python Boto v 2.9.8
# see https://github.com/boto/boto
# Requires these to be set
# AWS_ACCESS_KEY_ID
# AWS_DEFAULT_REGION
# AWS_SECRET_ACCESS_KEY

import boto.ec2

from socket import gethostbyaddr
from optparse import OptionParser
from boto.s3.connection import S3Connection
from boto.ec2.elb import ELBConnection

class instance_enum():
    def __init__(self,tag_hosts=False,private_hosts=False,resolve_hosts=False):
        self.resolve_hosts = resolve_hosts
        self.tag_hosts = tag_hosts
        self.private_hosts = private_hosts
        self.regions = []
        self.instance_dict = {} # key is region_name 
        self.addrs = []
        self.name_dict = {} # d["4.4.4.4"] = "a.b.com"

        for r in boto.ec2.regions():
            self.regions.append(r.connect())

        for r in self.regions:
            if self.tag_hosts:
                for res in r.get_all_instances():
                    for i in res.instances:
                        tag_dict = i.tags

                        if self.private_hosts:
                          host_ip = i.private_ip_address
                        else:
                          host_ip = i.ip_address

                        if tag_dict:
                          self.name_dict[host_ip] = tag_dict['Name']
                        else:
                          self.name_dict[host_ip] = 'unknown'
            for a in r.get_all_addresses():
                self.addrs.append(a)

    def get_hosts(self):
        hosts = []

        # For EIPs
        for a in self.addrs:
            if a.instance_id:

                if self.private_hosts:
                  host_ip = a.private_ip_address
                else:
                  host_ip = i.ip_address

                if self.tag_hosts:
                  hosts.append(host_ip+","+self.name_dict[host_ip])
                else:
                    hosts.append(host_ip)
        # The rest of the instances

        for r in self.regions:
          for res in r.get_all_instances():
              for i in res.instances:
                host_ip = i.private_ip_address
                if self.tag_hosts:
                  hosts.append(host_ip+","+self.name_dict[host_ip])

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
        urls = []
        for l in self.lbs:
            for li in l.listeners:
                if li.instance_protocol == "HTTP":
                    url = "%s://%s" % ('http',l.dns_name)
                if li.instance_protocol == "HTTPS":
                    url = "%s://%s" % ('https',l.dns_name)
                if url not in urls:
                    urls.append(url)
        return urls
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
    parser.add_option("-i","--ip",action="store_true",dest="ip",default=False, help="Dump L3 addresses")
    parser.add_option("-v","--verbose",action="store_true",dest="verbose",default=True, help="Verbose output")
    parser.add_option("-u","--url",action="store_true",dest="url",default=False,help="Dump URLs")
    parser.add_option("-s","--sql",action="store_true",dest="sql",default=False,help="Dump Database Connection")
    parser.add_option("-n","--noresolv",action="store_true",dest="noresolv",default=True,help="Do not perform DNS resolution")
    parser.add_option("-t","--tag",action="store_true",dest="tag",default=False,help="Return tags for instances")
    parser.add_option("-p","--private",action="store_true",dest="private",default=False,help="Return Private IPs (not EIP)")

    (options,args) = parser.parse_args()

    regions = []
    hosts = []
    urls = []

    for r in boto.ec2.regions():
        regions.append(r.connect())

    elb = elb_enum(ELBConnection())

    if options.ip:
        ec2 = instance_enum(options.tag,options.private)

        all_hosts = [ elb.get_hosts() , ec2.get_hosts() ]

        for src in all_hosts:
            for h in src:
                if h not in hosts:
                    hosts.append(h)
        for h in sorted(hosts):
            print h
    if options.url:
        s3 = s3_enum(S3Connection())
        all_urls = [ s3.get_urls(), elb.get_urls() ]

        for src in all_urls:
            for u in src:
                if u not in urls:
                    urls.append(u)

        for u in sorted(urls):
            print u

