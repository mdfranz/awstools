#!/usr/bin/env python

VERBOSE=True
CLEANUP=True

import ConfigParser,sys,netaddr,time
import boto.ec2,boto.vpc,boto.ec2.elb
import logging
from boto.ec2.elb import HealthCheck

def block_service(service,max_attempts=5,sleep=3):
    attempt = 0
    while service.state != 'pending' and (attempt < max_attempts):
        print service.state
        attempt += 1
        if VERBOSE:
            print "Waiting for service to come up"
        time.sleep(sleep)

if __name__ == "__main__":
    logging.basicConfig(filename="boto.log", level=logging.DEBUG)

    if len(sys.argv) < 2:
        print "usage:\n\t buildmyvpc.py foo.ini"
        sys.exit(-1)

    # Get configuration elements
    cs = ConfigParser.ConfigParser()
    cs.read(sys.argv[1])
    region = cs.get('vpc','region')
    subnet_size = cs.get('vpc','subnet_size')
    elb_name = cs.get('elb','name')
    sg_name = cs.get('elb','secgroup')
    netblock = netaddr.IPNetwork(cs.get('vpc','netblock'))
    subnet_count = int(cs.get('vpc','subnet_count'))
   
    # Create the VPC
    vpc_conn = boto.vpc.connect_to_region(region)
    ec2_conn = boto.ec2.connect_to_region(region)
    my_routes = vpc_conn.get_all_route_tables()
    my_vpc = vpc_conn.create_vpc(str(netblock))
    my_addr = ec2_conn.get_all_addresses()   # Get all the EIPs i own

    if VERBOSE:
        print "Existing VPCs"
        for vpc in vpc_conn.get_all_vpcs():
            print vpc.id,vpc.cidr_block

    all_subnets = list(netblock.subnet(int(subnet_size)))

    # Create the Internet Gateway
    my_gateway = vpc_conn.create_internet_gateway()

    if VERBOSE:
        print "Creating VPC (%s) in %s in %s" % (my_vpc.id,region,str(netblock))
        print "Creating Internet Gateway: %s" % (my_gateway.id)

    my_subnets = []

    # Create the subnets
    for s in all_subnets[1:subnet_count+1]:
        if VERBOSE:
            print "Creating subnet %s" % (str(s))
            my_subnets.append(vpc_conn.create_subnet(my_vpc.id,str(s)))

    # Attach gateway
    vpc_conn.attach_internet_gateway(my_gateway.id,my_vpc.id)

    # Dump routes while we are at it
    if VERBOSE:
        for r in my_routes:
            if r.vpc_id == my_vpc.id:
                print r.routes

    # On to the ELB
    elb_conn = boto.ec2.elb.connect_to_region(region)
    elb_sg = vpc_conn.create_security_group(sg_name+"-elb","Squid ELB Security Group",my_vpc.id)
    elb_sg.authorize('tcp',3128,3128,str(netblock))
    squid_subnet = my_subnets[0]

    sys.exit(-1)

    # Create private ELB that allows the entire VPC to connect to it
    my_elb = elb_conn.create_load_balancer(elb_name,None,[(3128, 3128, 'tcp')],[my_subnets[0].id],[elb_sg.id],'internal')

    if VERBOSE:
        print "Created LoadBalancer: %s" % (my_elb.dns_name)

    instance_sg = vpc_conn.create_security_group(sg_name,"Squid Instance Security Group",my_vpc.id)
    instance_sg.authorize('tcp',3128,3128,str(netblock))
    instance_sg.authorize('tcp',22,22,"0.0.0.0/0")

    if VERBOSE:
        print "Creating instances on subnet: %s" % (squid_subnet.id)

    # Create 2 instances and add to LB pool and place on the x.x.1.x subnet

    # run_instances(self, image_id, min_count=1, max_count=1, key_name=None, security_groups=None, user_data=None, addressing_type=None, instance_type='m1.small', placement=None, kernel_id=None, ramdisk_id=None, monitoring_enabled=False, subnet_id=None

    reservation = vpc_conn.run_instances( cs.get("instances","ami"), 2, 2, cs.get("instances","key"),[instance_sg.id],None,None,cs.get("instances","type"),None,None,None,False,my_subnets[0].id )

    for i in reservation.instances:
        if VERBOSE:
            print ("Created id: %s ip: %s") % (i.id, i.private_ip_address)

    if CLEANUP: 
        for i in reservation.instances:
            i.terminate()

        elb_conn.delete_load_balancer(elb_name)

        for s in my_subnets:
            vpc_conn.delete_subnet(s.id)
        vpc_conn.detach_internet_gateway(my_gateway.id,my_vpc.id)
        my_vpc.delete() 
