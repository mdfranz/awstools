#!/usr/bin/env python

#
# Simple script for dumping targets for external AWS vuln scans
# Assumes boto variables are set: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
#

import boto.vpc,sys,boto,boto.ec2,socket,boto.ec2.elb

def dump_vpc_hosts(c,vpc_id=None):
  for res in c.get_all_instances():
    for i in res.instances:  
      if i.vpc_id:
        if i.tags.has_key("Name"):
          identifier = i.tags["Name"]
        else:
          identifier = "Undefined"

        if vpc_id:
          if i.vpc_id == vpc_id:
              print "%s,%s" % ( i.private_ip_address, identifier)
        else:
          print "%s,%s" % ( i.private_ip_address, identifier)

if __name__ == "__main__":
  conn = boto.ec2.EC2Connection()
  regions = conn.get_all_regions()
  account_id =  conn.get_all_security_groups(groupnames='default')[0].owner_id

  vpc_list = []

  for r in regions:
    c = boto.ec2.connect_to_region(r.name)
    v = boto.vpc.connect_to_region(r.name)
    e = boto.ec2.elb.connect_to_region(r.name)

    if not c:
      continue      

    if len(sys.argv) == 1:
      print "Usage:\n\tawsnetshow.py [hosts|vpcs|elbs|all|vpcid|privatehosts]"
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
              identifier = "Undefined"

            hosts.append( (account_id,r.name, i.ip_address,identifier) )

      for i in c.get_all_addresses():
        if i.public_ip:
          # Avoid duplicates if we've seen already
          if not  i_dict.has_key(i.instance_id):
            hosts.append( (account_id,r.name, i.public_ip,"Undefined") )

      for h in hosts :
        print "%s,%s,%s,%s" % ( h[0],h[1], h[2],h[3] )

    if "vpcs" in sys.argv or "all" in sys.argv:
      for i in v.get_all_vpcs():
        if i.tags.has_key("Name"):
          identifier = i.tags["Name"]
        else:
          identifier = "Undefined"
        print "%s,%s,%s,%s,%s" % (account_id,r.name, i.cidr_block,i.id,identifier)

    if "elbs" in sys.argv or "all" in sys.argv:
      for lb in e.get_all_load_balancers():
          print "%s,%s,%s,None" % (account_id,r.name, lb.dns_name)

    if sys.argv[1] == "privatehosts":
      dump_vpc_hosts(c)

    if sys.argv[1] not in  ['all','hosts','elbs','privatehosts']:
      vpc_list = []
      for i in v.get_all_vpcs():
        vpc_list.append(i.id)

      if sys.argv[1] in vpc_list:
        dump_vpc_hosts(c,sys.argv[1])




