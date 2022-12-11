#!/usr/bin/env python3

import boto3,sys,string,time,socket

if __name__ == "__main__":
  if len(sys.argv) == 1:
    print ("./clean_functions.py <region|all>")
  else:
    ec2 = boto3.client('ec2')

    regions = []
    if sys.argv[1] != "all":
      regions = [ sys.argv[1] ] 
    else:
      for r in ec2.describe_regions()['Regions']:
        regions.append(r['RegionName'])

    for r in regions:
      b =  boto3.client('lambda',region_name=r)

      for f in b.list_functions()['Functions']:
        print ("Deleting "+ f['FunctionName'])
        b.delete_function(FunctionName=f['FunctionName'])
    




