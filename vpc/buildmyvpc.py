#!/usr/bin/env python

VERBOSE=True
CLEANUP=True

import ConfigParser,sys,netaddr,time
import boto.ec2,boto.vpc
import logging

def block_service(service,max_attempts=5,sleep=3):
    attempt = 0
    while service.state != 'pending' and (attempt < max_attempts):
        print service.state
        attempt += 1
        if VERBOSE:
            print "Waiting for service to come up"
        time.sleep(sleep)

# Not sure why I had to do this, seems like I shouldn't have to

if __name__ == "__main__":
    logging.basicConfig(filename="boto.log", level=logging.DEBUG)

    if len(sys.argv) < 2:
        print "usage:\n\t buildmyvpc.py foo.ini"
        sys.exit(-1)

    # Get configuration elements
    cs = ConfigParser.ConfigParser()
    cs.read(sys.argv[1])
    region = cs.get('vpc','region')
    netblock = netaddr.IPNetwork(cs.get('vpc','netblock'))
    subnet_count = int(cs.get('vpc','subnet_count'))
   
    # Create the VPC
    vpc_conn = boto.vpc.connect_to_region(region)
    my_vpc = vpc_conn.create_vpc(str(netblock))

    if VERBOSE:
        print "Existing VPCs"
        for vpc in vpc_conn.get_all_vpcs():
            print vpc.id,vpc.cidr_block

    #block_service(my_vpc)

    if VERBOSE:
        print "Creating VPC in %s in %s" % (region,str(netblock))

    all_subnets = list(netblock.subnet(24))
    my_gateway = vpc_conn.create_internet_gateway()
    vpc_conn.attach_internet_gateway(my_gateway.id,my_vpc.id)

    my_subnets = []
    for s in all_subnets[1:subnet_count+1]:
        if VERBOSE:
            print "Creating subnet %s" % (str(s))
            my_subnets.append(vpc_conn.create_subnet(my_vpc.id,str(s)))

    if CLEANUP: 
        for s in my_subnets:
            vpc_conn.delete_subnet(s.id)
        vpc_conn.detach_internet_gateway(my_gateway.id,my_vpc.id)
        my_vpc.delete() 
