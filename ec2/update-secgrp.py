#!/usr/bin/env python

DEBUG=True
DELETE=False

import boto,os,sys,netaddr,boto.ec2

usage = """$ update-secgrp <sg-id> <rule> <filename>

Adds all the netlbocks in the given file to the security group specified
and validates network blocks using python netaddr.

Examples:
  $ update-secgrp.py sg-foo tcp/22 hostlist
  $ update-secgrp.py sg-foo tcp/22 hostlist revoke
  $ update-secgrp.py tcp/22-23 hostlist
  $ update-secgrp.py list -- dumps all in region

"""
#AWS_ACCESS_KEY_ID = ''
#AWS_SECRET_ACCESS_KEY = ''
#AWS_DEFAULT_REGION

def create_block_list(f):
  blocks = []
  for i in open(f):
    try:
      block = netaddr.IPNetwork(i.rstrip())
      blocks.append(block.__str__())
    except:
      print "Ignoring Bad Netblock: %s" % i
  return blocks

def check_sg(sglist,sg):
  for s in sglist:
    if sg == s.id:
      return s
  return None

def convert_rule(s):
  rule = {}
  rules = s.split('/')
  rule['protocol'] = rules[0]
  ports = rules[1].split('-')
  rule['start_port'] = ports[0]

  if len(ports) > 1:
    rule['end_port'] = ports[1]
  else:
    rule['end_port'] = ports[0]
  return rule

if __name__ == "__main__":
  # Too lazy to do something with OptionParser or ArgParser so sue me

  if len(sys.argv) < 2:
    print usage
    sys.exit(-1)
  else:

    # Handle regions
    if os.environ.has_key("AWS_DEFAULT_REGION"):
      e = boto.ec2.connect_to_region(os.environ["AWS_DEFAULT_REGION"])
    else:
      e = boto.connect_ec2()

    sec_groups = e.get_all_security_groups()

    if len(sys.argv) == 2:
      for s in sec_groups:
        print "%s | %s | %s " % (s.id,s.vpc_id,s.name)
      sys.exit(-1)
    elif len(sys.argv) > 3:
      sg_target = sys.argv[1]
      rule = sys.argv[2]
      netfile = sys.argv[3]
    else:
      print usage
      sys.exit(-1)

    if len(sys.argv) == 5:
      if sys.argv[4] == "revoke":
        DELETE=True

    ### Main logic is right here
    my_group = check_sg(sec_groups,sg_target)
    if not my_group:
      print "%s not found!" % sg_target
      sys.exit(-1)
    else: 
      print "Updating: %s (%s)  %s " % (my_group.id,my_group.vpc_id,my_group.name)

    # Validate the lists of netblocks
    valid_nets = create_block_list(netfile)
    new_rule = convert_rule(rule)

    # Create rules for 
    for n in valid_nets:
      try:
        if DELETE:
          my_group.revoke( ip_protocol=new_rule['protocol'], from_port=new_rule['start_port'], to_port=new_rule['end_port'], cidr_ip=n)
        else:
          my_group.authorize( ip_protocol=new_rule['protocol'], from_port=new_rule['start_port'], to_port=new_rule['end_port'], cidr_ip=n)
      except Exception as e:
        # Handle duplicates
        print "Unable to add/delete rule\n\n", e
