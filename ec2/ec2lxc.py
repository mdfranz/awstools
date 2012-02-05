#!/usr/bin/env python

# Set these
#AWS_ACCESS_KEY_ID = ''
#AWS_SECRET_ACCESS_KEY = ''
#AWS_SSH_PEM=''
AMI = "ami-e358958a"
AMI_TYPE = "t1.micro"
DEBUG=True

import boto,time,sys,os,tempfile

# TODO actually test this
try:
    import paramiko as ssh
except:
    import ssh
    
### Top level stuff

chef_bootscript="""#!/usr/bin/env bash
export DEBIAN_FRONTEND=noninteractive 
apt-get -y update
apt-get -y install chef
mkdir -p /var/chef/cookbooks
chef-solo -ldebug
"""

def sho_run(e):
    """Dump out all the instances per reservation"""
    r = e.get_all_instances()
    for s in r:
        for i in s.instances:
            print i.public_dns_name, i.launch_time, i.state

### The real work

if __name__ == "__main__":
    print "Connecting to EC2..."
    e = boto.connect_ec2()

    if len(sys.argv) == 1:
        sho_run(e)
        sys.exit()

    if sys.argv[1] == "start":

        # Create new minimal AWS Linux AMI
        ssh1 = os.environ['AWS_SSH_PEM'].split('/')[-1]
        ssh2 = ssh1.split('.')[0]

        # Get the reservation
        r = e.run_instances(AMI,key_name=ssh2,instance_type=AMI_TYPE)

        print "Creating instance in:",r.region.name

        i = r.instances[-1]
        print "Launch time:",i.launch_time
        time.sleep(5)

        # Dump all the instances
        while i.state != "running":
            i.update()
            print "State:",i.state
            time.sleep(5)

        host = i.public_dns_name
        print "Host name:",host

        # Create the bootstrap file
        boot_file = tempfile.NamedTemporaryFile()
        boot_file.write(chef_bootscript)
        boot_file.flush()
        print "Creating:\n",boot_file.name

        print "Waiting 30 seconds for SSH"
        time.sleep(30)

        # Create the channel
        sclient = ssh.SSHClient()
        sclient.set_missing_host_key_policy(ssh.AutoAddPolicy())
        sclient.connect(host, username='ubuntu', key_filename=os.environ['AWS_SSH_PEM'])
        print "Connected to: %s" % host  

        # Get git
        (stdin, stdout, stderr) = sclient.exec_command('sudo apt-get -y update; sudo apt-get -y install git-core')
        print stdout.readlines()

        sftpclient = ssh.SFTPClient.from_transport(sclient.get_transport())
        sftpclient.put(boot_file.name,"/tmp/chefboot.sh")
        print `sftpclient.listdir('/tmp')`

        # Install Chef
        (stdin, stdout, stderr) = sclient.exec_command('sudo sh /tmp/chefboot.sh')
        print stdout.readlines()

        sclient.close()

    elif sys.argv[1] == "stop":
        r = e.get_all_instances()
        for s in r:
            for i in s.instances:
                print "Host name:",i.public_dns_name, i.state

                if i.state != "terminated":
                    while i.state != "terminated":
                        try:
                            i.stop()
                        except:
                            pass 

                        i.update()

                        print "State:",i.state
                        time.sleep(5)
                        i.terminate()
                print "State:",i.state
    else:
        sho_run(e)
