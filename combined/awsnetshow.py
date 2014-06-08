#!/usr/bin/env python

#
# Simple script for dumping targets for external AWS vuln scans
# Assumes boto variables are set: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
#

import boto.vpc,sys,boto,boto.ec2,socket,boto.ec2.elb

conn = boto.ec2.EC2Connection()
regions = conn.get_all_regions()
account_id =  conn.get_all_security_groups(groupnames='default')[0].owner_id

for r in regions:
  c = boto.ec2.connect_to_region(r.name)
  v = boto.vpc.connect_to_region(r.name)
  e = boto.ec2.elb.connect_to_region(r.name)

  if len(sys.argv) == 1:
    print "Usage:\n\tawsnetshow.py [hosts|vpcs|elbs|all]"
    sys.exit(-1)

  if "hosts" in sys.argv or "all" in sys.argv:
    i_dict = {}
    hosts = []  # will probably be duplicates here but uniq them out


    for res in c.get_all_instances():
      for i in res.instances:  
        # Skip private addresses
        if i.ip_address:


          if i.tags.has_key("Name"):
            identifier = i.tags["Name"]
            i_dict[i.id] = identifier
          else:
            identifier = i.id

          hosts.append( (account_id,r.name, i.ip_address,identifier) )

    for i in c.get_all_addresses():
      if i.public_ip:

        # Avoid duplicates if we've seen already
        if not  i_dict.has_key(i.instance_id):
          hosts.append( (account_id,r.name, i.public_ip,i.instance_id) )

    for h in hosts :
      print "%s,%s,%s,%s" % ( h[0],h[1], h[2],h[3] )

  if "vpcs" in sys.argv or "all" in sys.argv:
    for i in v.get_all_vpcs():
        print "%s,%s,%s,%s" % (account_id,r.name, i.cidr_block,i.id)

  if "elbs" in sys.argv or "all" in sys.argv:
    for lb in e.get_all_load_balancers():
        print "%s,%s,%s,None" % (account_id,r.name, lb.dns_name)
