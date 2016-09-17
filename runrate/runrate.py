#!/usr/bin/env python

import boto.vpc,sys,boto,boto.ec2,socket,boto.rds

pricing = {}

def bar_tuple(t,accountid):
    """Print pretty line for csv import into .xls"""
    t.insert(0,str(accountid))
    for c in t:
        print " | " + str(c),
    print " |"

def running_days(ltime):
    lt_datetime = datetime.datetime.strptime( ltime.split('.')[0], '%Y-%m-%dT%H:%M:%S')
    lt_delta = datetime.datetime.utcnow() - lt_datetime
    return str(lt_delta.days)

def sum_volumes(vlist):
    for v in vlist:
        size =+ v.size
    return size
    
def get_systems(c,tag_string=None,running_only=True):
    """Get instance data including ec2 and ebs"""
    hosts = []
    volumes = {}
    if c:
        for v in c.get_all_volumes():
            if v.status == "in-use":
                if v.attach_data.instance_id in volumes:
                    volumes[v.attach_data.instance_id].append(v)
                else:
                    volumes[v.attach_data.instance_id] = [ v ]

    for res in c.get_all_instances():
       for i in res.instances:  
            if running_only:
                if i.state != "running":
                    continue
            if i.tags.has_key("Name"):
                identifier = i.tags["Name"]
            else:
                identifier = "Undefined"

            hosts.append( [ "ec2", r.name, identifier, i.instance_type, sum_volumes(volumes[i.id])],running_days(i.launch_time) )

    return hosts

def get_dbs(c):
    hosts = []
    for i in c.get_all_dbinstances():
        if i.status == "available":
            if i.multi_az:
                redundancy = "multi_az"
            else:
                redundancy = "single_az"

        hosts.append( [ "rds", i.availability_zone[:-1], i.endpoint[0], i.instance_class, i.allocated_storage, i.engine, redundancy ] )
    return hosts

if __name__ == "__main__":
    conn = boto.ec2.EC2Connection()
    regions = conn.get_all_regions()
    account_id =  conn.get_all_security_groups(groupnames='default')[0].owner_id

    if len(sys.argv) == 0:
        print "Usage:\n\trunrate.py <region>"
        sys.exit(-1)
    else:
        for r in regions:
            if sys.argv[1] != "all":
                if sys.argv[1] != r.name:
                    continue
            c = boto.ec2.connect_to_region(r.name)
            for h in get_systems(c):
                bar_tuple(h,account_id)

            c = boto.rds.connect_to_region(r.name)
            if c: 
                db_instances = get_dbs(c)
                if db_instances:
                    for h in db_instances:
                        bar_tuple(h,account_id)

