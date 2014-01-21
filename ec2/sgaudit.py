#!/usr/bin/env python

import boto,boto.vpc,os,socket,netaddr,json,time

class NetDecorator(object):
  """Adds various metadata to a network source"""
 
  def __init__(self,conn,debug=True):
    self.private_hosts = {}
    self.public_hosts = {}
    self.dns_cache = {}
    self.vpcs = {}
    self.debug = debug

    # Build list of Names
    for res in conn.get_all_instances():
      for i in res.instances:
        if 'Name' in i.tags:
          if self.debug:
            print "Found",i.tags['Name']
          if i.private_ip_address:
            self.private_hosts[i.private_ip_address] = i.tags['Name']
          if i.public_dns_name:
            self.public_hosts[i.public_dns_name] = i.tags['Name']

    # Get the VPCs
    for vpc in conn.get_all_vpcs():
      self.vpcs[vpc.cidr_block] = vpc

  def resolve(self,i):
    """Attempt reverse lookup, add aws region or perform whois"""
    host = i

    if host in self.dns_cache:
      if self.debug: 
        print "Found %s in DNS cache" % s

      hostname = self.dns_cache[host]
      #self.nodes[r[0]][r[1]].append(self.dns_cache[host])
    else:
      try:
        resolved_host = socket.gethostbyaddr(host)[0]

        if resolved_host.find("amazonaws") > 0:
          hostname = resolved_host.split('.')[1]
        else:
          hostname = resolved_host
          
      except Exception as e: 
        if self.debug:
          print "Error:",e
        hostname = host
    return hostname

  def get_name(self,i):
    """Check for name tag"""
    pass

  def get_vpc(self,i):
    """Return the VPC ID"""
    pass


  def decorate_host(self,i):
    ipaddr = str(i.ip)
    if not i.is_private():
      return ipaddr + "|" + self.resolve(ipaddr)
    else:
      if ipaddr in self.private_hosts:
        return ipaddr + "|" + self.private_hosts[ipaddr]
      else:
        return ipaddr

class AuditGroup(object):
  """Wrapper for Boto Security Group with Audit Capabilities"""

  def __init__(self,boto_sg,debug=True):
    self.sg = boto_sg
    self.name = boto_sg.name

    self.cidr_sources = {}
    self.sg_sources = {}

    for r in self.sg.rules:

      # Right now only handle port based flow, no ICMP
      if r.ip_protocol not in ['tcp','udp']:
        continue

      if r.from_port == r.to_port:
        port_range = r.ip_protocol + "/" + r.from_port
      else:
        port_range = r.ip_protocol + "/" + r.from_port + "-" + r.to_port

      for g in r.grants:
        if g.cidr_ip:
          if not port_range in self.cidr_sources:
            self.cidr_sources[port_range] = []
          self.cidr_sources[port_range].append(g.cidr_ip)
        elif g.group_id:
          if not port_range in self.sg_sources:
            self.sg_sources[port_range] = []

          self.sg_sources[port_range].append(g.group_id)

  def get_cidr_rules(self):
    """Return CIDR sources accessing this SG"""
    rules = []
    for r in self.cidr_sources.keys():
      for s in self.cidr_sources[r]:
        rules.append((r,s))
    return rules

  def get_sg_rules(self):
    """Return other security groups that access SG"""
    rules = []
    for r in self.sg_sources.keys():
      for s in self.sg_sources[r]:
        rules.append((r,s))
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

  def __init__(self,sg_dict,decorator,debug=True):
    self.nodes = {}
    self.sg_dict = sg_dict
    self.debug = debug
    self.decorator = decorator

    if self.debug:
      print "Adding rules"

    for sg in sg_dict.keys():
      for r in sg_dict[sg].get_rules():

        if self.debug:
          print "-" + sg_dict[sg].name,r

        self.add_rule_tuple((sg_dict[sg].name,r[0],r[1]))

  def add_rule_tuple(self,r):
    if self.debug:
      print "PROCESSING:", r

    if r[0] not in self.nodes:
      self.nodes[r[0]] = {}

    if r[1] not in self.nodes[r[0]]:
      self.nodes[r[0]][r[1]] = []
   
    # Add entry for security group sources
    if r[2] in self.sg_dict:
      if self.debug:
        print "Adding security group"
      self.nodes[r[0]][r[1]].append(self.sg_dict[r[2]].name)

    # Everything else is a network object
    else:
      ip = netaddr.IPNetwork(r[2]) 

      if self.debug:
        print "Evaluating ",ip

      if ip.size == 1:
        self.nodes[r[0]][r[1]].append(self.decorator.decorate_host(ip))

        #self.nodes[r[0]][r[1]].append(hostname)
      else:
        pass

  def get_protocols(self):
    protocols = []
    for s in self.get_dests():
      for p in self.nodes[s].keys():
        if p not in protocols:
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
    for resource in self.nodes.keys():
      for port in self.nodes[resource].keys():
        for source in self.nodes[resource][port]:
          print "%s,%s,%s " % (resource,port,source)


   
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

  d = NetDecorator(conn,False)
  fg = FlowGraph(sg_dict,d,False)
  fg.to_grep()
