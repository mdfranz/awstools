#!/usr/bin/env python

###############################################################
# Assumes these are Set

#AWS_ACCESS_KEY_ID = ''
#AWS_SECRET_ACCESS_KEY = ''
#AWS_SSH_PEM=''

###############################################################

import boto,time,sys,os,tempfile

# TODO actually test this
try:
    import paramiko as ssh
except:
    import ssh

###############################################################

SSH_MAXCOUNT = 10
AMI_SIZE = "t1.micro"
DEFAULT_OS = "natty"
DEBUG=True

###############################################################
# These are all us-east and i386 and t1.micro
###############################################################

instances = {}
instances["freebsd"] = ['ami-b55f99dc']
instances["natty"] = ['ami-e358958a']
instances["aws"] = ['ami-31814f58']

# Usernames of these OS, which are all different
os_user = {}
os_user['natty'] = 'ubuntu'
os_user['aws'] = 'ec2-user'
os_user['freebsd'] = 'root'

###############################################################
# Chef bootstrapping 
###############################################################

chef_strap = {}
nodes = {}

chef_strap["aws"] = """#!/usr/bin/env bash
yum -y install ruby-devel make gcc rubygems git
"""

chef_strap["natty"] = """#!/usr/bin/env bash
export DEBIAN_FRONTEND=noninteractive 
apt-get -y update
apt-get -y install chef
"""

chef_strap["freebsd"] = """#!/usr/bin/env bash
pkgadd -vr rubygems-chef sudo
"""

git_cookbooks="""
mkdir -p /var/chef/cookbooks
git clone git://github.com/mdfranz/cookbooks.git
cp -av cookbooks/lxc /var/chef/cookbooks/
"""

# TODO fix this and add through cli

# Chef Node file for only LXC
nodes["lxc"]="""
{
        "run_list": "lxc"
}
"""

##############################################################

def ssh_boot(s,os=DEFAULT_OS,debug=DEBUG):
    """Run commands to boot AMI"""
    # Create the bootstrap file


    boot_file = tempfile.NamedTemporaryFile()
    boot_file.write(chef_strap[os])
    boot_file.flush()

    if debug:
        print "Creating:\n",boot_file.name
        print chef_strap[os]

    # Create the node_json
    #node_file = tempfile.NamedTemporaryFile()
    #node_file.write(node_json)
    #node_file.flush()

    if debug:
        #print "Creating:\n",node_file.name
        print "Installing git..."

    # Get git

    if os == "aws":
        command = 'sudo yum -y install git'
    elif os == "freebsd":
        command = 'pkgadd -vr git'
    else:
        command = 'sudo apt-get -y update; sudo apt-get -y install git-core'

    (stdin, stdout, stderr) = s.exec_command(command)

    if debug:
        print stdout.readlines()

    # Upload Bootstrap Chef Solo
    sftpclient = ssh.SFTPClient.from_transport(s.get_transport())
    sftpclient.put(boot_file.name,"/tmp/chefboot.sh")

    # Install Chef
    (stdin, stdout, stderr) = s.exec_command('sudo sh /tmp/chefboot.sh')

    if debug:
        print "Out:",stdout.readlines()
        print "Err:",stderr.readlines()

    #sftpclient.put(node_file.name,"/home/ubuntu/node.json")
    #(stdin, stdout, stderr) = s.exec_command('sudo chef-solo -j /home/ubuntu/node.json')
    #if debug:
        print stdout.readlines()

def sho_run(e):
    """Dump out all the instances per reservation"""
    r = e.get_all_instances()
    for s in r:
        for i in s.instances:
            print i.public_dns_name, i.private_ip_address, i.launch_time, i.state

### The real work

if __name__ == "__main__":
    if DEBUG:
        print "Connecting to EC2..."
    e = boto.connect_ec2()

    print `sys.argv`

    if len(sys.argv) == 1:
        sho_run(e)
        sys.exit()

    if sys.argv[1] == "start":
        if len(sys.argv) > 2:
            os_type = sys.argv[2]

            if os_type not in instances.keys():
                os_type = DEFAULT_OS
        else:
            os_type = DEFAULT_OS

        if DEBUG:
            print "Creating %s instance" % os_type

        # Create new minimal 
        ssh1 = os.environ['AWS_SSH_PEM'].split('/')[-1]
        ssh2 = ssh1.split('.')[0]


        # Get the reservations
        r = e.run_instances(instances[os_type][0],key_name=ssh2,instance_type=AMI_SIZE)
        print "Creating instance in:",r.region.name

        i = r.instances[-1]
        print "Launch time:",i.launch_time

        if DEBUG:
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
                if DEBUG:
                    print "Attempting to connect to %s as %s" % (i.public_dns_name,os_user[os_type])
                    sclient.connect(i.public_dns_name, username=os_user[os_type], key_filename=os.environ['AWS_SSH_PEM'])
                    break
            except:
                ssh_count+=1
                wait_time = ssh_count * 2
                print "Cannot connect to %s waiting for %d seconds" % (i.public_dns_name,wait_time)
                time.sleep(wait_time)

        print "Connected to: %s" % i.public_dns_name

        ssh_boot(sclient,os_type)
        sclient.close()
        print "Host name assigned:",i.public_dns_name
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
