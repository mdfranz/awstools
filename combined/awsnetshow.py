#!/usr/bin/env python

import boto.vpc,sys, boto, boto.ec2,socket,boto.ec2.elb

conn = boto.ec2.EC2Connection()
regions = conn.get_all_regions()
account_id =  conn.get_all_security_groups(groupnames='default')[0].owner_id


for r in regions:
  c = boto.ec2.connect_to_region(r.name)
  v = boto.vpc.connect_to_region(r.name)
  e = boto.ec2.elb.connect_to_region(r.name)

  if "eip" in sys.argv or "all" in sys.argv:
    for i in c.get_all_addresses():
       print "%s,%s,%s,%s" % (account_id,r.name, i.public_ip,i.instance_id)

  if "vpc" in sys.argv or "all" in sys.argv:
    for i in v.get_all_vpcs():
        print "%s,%s,%s,%s" % (account_id,r.name, i.cidr_block,i.id)

  if "elb" in sys.argv or "all" in sys.argv:
    for lb in e.get_all_load_balancers():
        print lb.dns_name
        print "%s,%s,%s,None" % (account_id,r.name, lb.dns_name)
