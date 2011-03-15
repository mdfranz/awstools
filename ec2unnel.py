#!/usr/bin/env python

#AWS_ACCESS_KEY_ID = ''
#AWS_SECRET_ACCESS_KEY = ''

KEY_NAME = 'duo'
AMI = "ami-76f0061f"
AMI_TYPE = "t1.micro"

import boto,time,sys

def sho_run(e):
    """Dump out all the instances per reservation"""
    r = e.get_all_instances()
    for s in r:
        for i in s.instances:
            print i.public_dns_name, i.launch_time, i.state



#################################################################

if __name__ == "__main__":
    print "Connecting to EC2..."
    e = boto.connect_ec2()

    if len(sys.argv) == 1:
        sho_run(e)
        sys.exit()

    if sys.argv[1] == "start":
        # Create new minimal AWS Linux AMI
        r = e.run_instances(AMI,key_name=KEY_NAME,instance_type=AMI_TYPE)

        print "Creating instance in:",r.region.name

        i = r.instances[-1]
        print "Launch time:",i.launch_time
        time.sleep(5)
        while i.state != "running":
            i.update()
            print "State:",i.state
            time.sleep(5)
        print "Host name:",i.public_dns_name
    elif sys.argv[1] == "stop":
        r = e.get_all_instances()
        for s in r:
            for i in s.instances:
                if i.state == "running":
                    print "Host name:",i.public_dns_name

                    while i.state != "terminated":
                        i.stop()
                        i.update()
                        print "State:",i.state
                        time.sleep(5)
    else:
        sho_run(e)
