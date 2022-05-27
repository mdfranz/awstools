#!/usr/bin/env python3

import boto3,sys

if __name__ == "__main__":
  if len(sys.argv) < 1:
    print (sys.argv)

    print ("Usage:\n tag_instances <region> [target]")
    sys.exit(-1)

  my_region = sys.argv[1]

  ec2_client = boto3.client('ec2',region_name=my_region)
  ec2_resources = boto3.resource('ec2',region_name=my_region)

  print("Checking for mirror targets")
  print("Searching instances")

  # Find ENI's
  # Creating Target for ENIs
  # Mirror Session
