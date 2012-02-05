#!/usr/bin/env python

# Set these
#AWS_ACCESS_KEY_ID = ''
#AWS_SECRET_ACCESS_KEY = ''
#AWS_SSH_PEM=''

AMI = "ami-e358958a"
AMI_TYPE = "t1.micro"
DEBUG=True
SSH_MAXCOUNT=10

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
git clone git://github.com/mdfranz/cookbooks.git
cp -av cookbooks/lxc /var/chef/cookbooks/
"""

# Chef Node file for only LXC
node_json="""
{
        "run_list": "lxc"
}
"""

def ssh_boot(s,debug=True):
    """Run commands to boot AMI"""
    # Create the bootstrap file
    boot_file = tempfile.NamedTemporaryFile()
    boot_file.write(chef_bootscript)
    boot_file.flush()

    if debug:
        print "Creating:\n",boot_file.name

    # Create the node_json
    node_file = tempfile.NamedTemporaryFile()
    node_file.write(node_json)
    node_file.flush()

    if debug:
        print "Creating:\n",node_file.name

    # Get git
    (stdin, stdout, stderr) = s.exec_command('sudo apt-get -y update; sudo apt-get -y install git-core')

    if debug:
        print stdout.readlines()

    # Upload Bootstrap Chef Solo
    sftpclient = ssh.SFTPClient.from_transport(s.get_transport())
    sftpclient.put(boot_file.name,"/tmp/chefboot.sh")

    # Install Chef
    (stdin, stdout, stderr) = s.exec_command('sudo sh /tmp/chefboot.sh')


    if debug:
        print stdout.readlines()

    sftpclient.put(node_file.name,"/home/ubuntu/node.json")

    (stdin, stdout, stderr) = s.exec_command('sudo chef-solo -j /home/ubuntu/node.json')

    if debug:
        print stdout.readlines()


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
        # Create new minimal AWS Linux AMI (get key name)
        ssh1 = os.environ['AWS_SSH_PEM'].split('/')[-1]
        ssh2 = ssh1.split('.')[0]

        # Get the reservations
        r = e.run_instances(AMI,key_name=ssh2,instance_type=AMI_TYPE)
        print "Creating instance in:",r.region.name

        i = r.instances[-1]
        print "Launch time:",i.launch_time

        while i.state != "running":
            i.update()
            print "State:",i.state
            time.sleep(5)


        print "Host name assigned:",i.public_dns_name

        # Create the channel
        sclient = ssh.SSHClient()
        sclient.set_missing_host_key_policy(ssh.AutoAddPolicy())

        ssh_count = 1

        while ssh_count < SSH_MAXCOUNT:
            try:
                print "Attempting to connect to: ", i.public_dns_name
                sclient.connect(i.public_dns_name, username='ubuntu', key_filename=os.environ['AWS_SSH_PEM'])
                break
            except:
                ssh_count+=1
                wait_time = ssh_count * 2
                print "Cannot connect to %s waiting for %d seconds" % (i.public_dns_name,wait_time)
                time.sleep(wait_time)

        print "Connected to: %s" % i.public_dns_name

        ssh_boot(sclient)
        sclient.close()

    elif sys.argv[1] == "stop":
        r = e.get_all_instances()
        for s in r:
            for i in s.instances:
                if i.state != "terminated":
                    print "Host:",i.public_dns_name, i.state

                    while i.state != "terminated":
                        try:
                            i.stop()
                        except:
                            pass 

                        i.update()

                        print "State:",i.state
                        time.sleep(5)
                        i.terminate()
    else:
        sho_run(e)
