#!/usr/bin/env python

import boto,boto.vpc,os,socket,netaddr,json,time

class AuditGroup(object):
  """Wrapper for Boto Security Group with Audit Capabilities"""

  def __init__(self,boto_sg,debug=True):
    self.sg = boto_sg
    self.name = boto_sg.name

    self.cidr_sources = {}
    self.sg_sources = {}

    for r in self.sg.rules:

      rule_tuple = (r.ip_protocol,r.from_port,r.to_port)

      for g in r.grants:
        if g.cidr_ip:
          if not rule_tuple in self.cidr_sources:
            self.cidr_sources[rule_tuple] = []
          self.cidr_sources[rule_tuple].append(g.cidr_ip)
        elif g.group_id:
          if not rule_tuple in self.sg_sources:
            self.sg_sources[rule_tuple] = []

          self.sg_sources[rule_tuple].append(g.group_id)

  def get_cidr_rules(self):
    """Return CIDR sources accessing this SG"""
    rules = []
    for r in self.cidr_sources.keys():
      if r[0] not in ['tcp','udp']:
        continue
      for s in self.cidr_sources[r]:
        #print "%s/%s-%s " % ( r[0],r[1],r[2],s)
        rules.append((self.name,r[0]+"/"+r[1]+"-"+r[2],s))
    return rules

  def get_sg_rules(self):
    """Return other security groups that access SG"""
    rules = []
    for r in self.sg_sources.keys():
      if r[0] not in ['tcp','udp']:
        continue

      for s in self.sg_sources[r]:
        #print "%s/%s-%s " % ( r[0],r[1],r[2],s)
        rules.append((self.name,r[0]+"/"+r[1]+"-"+r[2],s))
    return rules

  def get_rules(self):
    rules = []

    for r in self.get_cidr_rules():
      rules.append(r)

    for r in self.get_sg_rules():
      rules.append(r)

    return rules

class FlowGraph(object):
  """Graph database for visualizing security groups"""

  def __init__(self,sg_dict,conn,debug=True):
    self.nodes = {}
    self.sg_dict = sg_dict
    self.vpc_dict = {} # vpc_dict[cidr] = vpc 
    # assume unique cidr
    self.dns_cache = {}
    self.debug = debug
    self.public_ip_dict = {}
    self.private_ip_dict = {}

    # Get VPC's so we can match on subnets for private IPs
    for vpc in conn.get_all_vpcs():
      self.vpc_dict[vpc.cidr_block] = vpc

    for res in conn.get_all_instances():
      for i in res.instances:
        if 'Name' in i.tags:
          if self.debug:
            print "Found",i.tags['Name']
          if i.private_ip_address:
            self.private_ip_dict[i.private_ip_address] = i.tags['Name']
          if i.public_dns_name:
            self.public_ip_dict[i.public_dns_name] = i.tags['Name']

    for sg in sg_dict.keys():
      for r in sg_dict[sg].get_rules():
        self.add_rule_tuple(r)

  def add_rule_tuple(self,r):
      # Process rules with sg

    if self.debug:
      print "PROCESSING:", r[0],r[1],r[2]

    if r[0] not in self.nodes:
      self.nodes[r[0]] = {}

    if r[1] not in self.nodes[r[0]]:
      self.nodes[r[0]][r[1]] = []
    
    if r[2] in self.sg_dict:
      self.nodes[r[0]][r[1]].append(self.sg_dict[r[2]].name)
    else:
      ip = netaddr.IPNetwork(r[2]) 

      if not ip.is_private():
        if ip.size == 1:
          try:
            host = str(ip.ip)

            if host in self.dns_cache:
              self.nodes[r[0]][r[1]].append(self.dns_cache[host])
            else:
              hostname = socket.gethostbyaddr(host)[0]

              if hostname.find("amazonaws.com") > 0:
                if self.debug:
                  print "AWS Host, need to lookup later"

              self.nodes[r[0]][r[1]].append(hostname)
              if self.debug:
                print "Found",hostname
              self.dns_cache[host] = hostname
          except Exception as e:
            if self.debug:
              print "Error:",e

            self.dns_cache[host] = host
            self.nodes[r[0]][r[1]].append(r[2])
        else:
          self.nodes[r[0]][r[1]].append(r[2])
      else:
        # Handle private hosts

        if ip.size == 1:
          host = str(ip.ip)
          if host in self.private_ip_dict:
            if self.debug:
              print "Found %s (%s)" % (host,self.private_ip_dict[host])
            self.nodes[r[0]][r[1]].append(r[2])
        else:
          if self.debug:
            print "Found private network, lets tie to VPC"

        self.nodes[r[0]][r[1]].append(r[2])

  def get_protocols(self):
    protocols = []
    for s in self.get_dests():
      for p in self.nodes[s].keys():
        if p not in protocols:

          p_split1 = p.split('/')[1]
          #print `p_split1`
          (sport,dport) = p_split1.split('-')

          if sport == dport:
            protocols.append(p.split('/')[0]+'/'+sport)
          else:
            protocols.append(p)
    return protocols
      
  def get_dests(self):
    dests = []
    for d in self.nodes.keys():
      if d not in dests:
        dests.append(d)
    return dests

  def get_sources(self):
    sources = []
    for d in self.nodes.keys():
      for p in self.nodes[d].keys():
        for s in self.nodes[d][p]:
          if s not in sources:  
            sources.append(s)
    return sources

  def to_dot(self,fname):
    """Dump to Graphviz File"""
    pass

  def add_group(self,sg):
    """Add security group to DB"""
    pass

  def to_csv(self,fname):
    """Dump to CSV"""
    pass

  def to_grep(self):
    """Dump to stdout for easy grepping"""

    for sg in sg_dict.keys():
      for r in sg_dict[sg].get_rules():
        print r


   
  def to_json(self,fname="Foo"):
    jdump = {}
    jdump['timestamp']  = time.time()
    jdump['sources'] = self.get_sources()
    jdump['protocols'] = self.get_protocols()
    jdump['dests'] = self.get_dests()

    print json.dumps(jdump)

if __name__ == "__main__":
  sg_dict = {}

  if "AWS_DEFAULT_REGION" in os.environ:
    conn = boto.vpc.connect_to_region(os.environ['AWS_DEFAULT_REGION'])
  else:
    conn = boto.connect_vpc()

  for sg in conn.get_all_security_groups():
    asg = AuditGroup(sg)
    sg_dict[asg.sg.id] = asg

  fg = FlowGraph(sg_dict,conn,False)

  print "\nDestinations"
  for d in fg.get_dests():
    print d

  print "\nProtocols"
  for p in fg.get_protocols():
    print p

  print "\nSources"
  for s in fg.get_sources():
    print s

  #fg.to_json()
  print `fg.public_ip_dict`
  print `fg.private_ip_dict`

  fg.to_grep()
