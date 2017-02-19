#!/usr/bin/env python

import boto.vpc,sys,boto,boto.ec2,socket,boto.rds,datetime,json,time,os

class PriceDict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)() # retain local pointer to value
        return value

pricing = PriceDict()
pricefile="/tmp/pricefile.json"
outputdir="/tmp/"
price_json = None

def bar_tuple(t,accountid):
    """Print pretty line for csv import into .xls"""
    t.insert(0,str(accountid))
    s=""
    for c in t:
        s = s + " | " + str(c)
    return(s+" |\n")

def running_days(ltime):
    lt_datetime = datetime.datetime.strptime( ltime.split('.')[0], '%Y-%m-%dT%H:%M:%S')
    lt_delta = datetime.datetime.utcnow() - lt_datetime
    return str(lt_delta.days)

def sum_volumes(vlist):
    for v in vlist:
        size =+ v.size
    return size

def guess_os(i):
    if i.key_name:
        return "Linux"
    else:
        if i.platform:
            return "Windows"
        else:
            return "Linux"

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

            if not price_json:
                pricing["ec2"][r.name][i.instance_type][guess_os(i)] = 0
                daily_cost = 0
            else:
                try:
                    daily_cost = price_json["ec2"][r.name][i.instance_type][guess_os(i)] * 24
                except Exception as e:
                    print "No rate for", e,identifier
                    daily_cost = 0

            hosts.append( [ "ec2", r.name, identifier, i.instance_type, (daily_cost * 365)/12, sum_volumes(volumes[i.id]), running_days(i.launch_time),guess_os(i) ] )

    return hosts

def get_dbs(c):
    hosts = []
    for i in c.get_all_dbinstances():
        if i.status == "available":
            if i.multi_az:
                redundancy = "multi_az"
            else:
                redundancy = "single_az"

            if not price_json:
                pricing["rds"][i.availability_zone[:-1]][i.instance_class][i.engine+"-"+redundancy] = 0
                daily_cost = 0
            else:
                try:
                    daily_cost = price_json["rds"][i.availability_zone[:-1]][i.instance_class][i.engine+"-"+redundancy] * 24

                except Exception as e:
                    print "No rate for ",i.endpoint[0],i.instance_class,redundancy, i.engine
                    daily_cost = 0

            hosts.append( [ "rds", i.availability_zone[:-1], i.endpoint[0], i.instance_class, (daily_cost*365)/12, i.allocated_storage, i.engine, redundancy ] )
    return hosts

if __name__ == "__main__":
    conn = boto.ec2.EC2Connection()
    regions = conn.get_all_regions()
    account_id =  conn.get_all_security_groups(groupnames='default')[0].owner_id

    if len(sys.argv) == 0:
        print "Usage:\n\trunrate.py <region>"
        sys.exit(-1)
    else:

        # Check for existing json file that continues prices per service/region/instance type
        if os.path.exists(pricefile):
            print "Found price template file"
            with open(pricefile) as f:
                price_json = json.load(f)
            print "Found values for:", price_json.keys()
            outfile = None
        else:
            # Otherwise generate a template that we can go in an populate manually from AWS pricing
            print "Generating new pricing templat"
            outfile = open(pricefile,"w")

        # Create "bar separated value" for each service and account
        rds_out = open(outputdir+account_id+"-rds-"+time.strftime("%Y-%m-%d.bsv"),"w")
        ec2_out = open(outputdir+account_id+"-ec2-"+time.strftime("%Y-%m-%d.bsv"),"w")

        rds_count = 0
        ec2_count = 0

        for r in regions:
            
            if sys.argv[1] != "all":
                if sys.argv[1] != r.name:
                    continue
            c = boto.ec2.connect_to_region(r.name)
            for h in get_systems(c):
                ec2_out.write( bar_tuple(h,account_id))
                ec2_count += 1

            c = boto.rds.connect_to_region(r.name)
            if c: 
                db_instances = get_dbs(c)
                if db_instances:
                    for h in db_instances:
                        rds_out.write( bar_tuple(h,account_id))
                        rds_count += 1

        # Create pricing template that can be populated later
        print "EC2 Found: ",ec2_count
        print "RDS Found: ",rds_count
       
        if outfile:
            json.dump(pricing,outfile,indent=2)
