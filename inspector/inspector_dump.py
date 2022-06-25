#!/usr/bin/env python3

# See https://github.com/grepcoffee/aws-scripts/blob/master/inspector/ListFindingsBySev/listfindings.py


import boto3,sys


if __name__ == "__main__":
  if len(sys.argv) > 1:
    my_region = sys.argv[1]
  else:
    my_region = "us-east-1"

  c = boto3.client("inspector",region_name=my_region)
  p = c.get_paginator("list_findings")

  for f in p.paginate():
    for arn in f['findingArns']:
      print (arn)
      print()
      for r in c.describe_findings(findingArns=[arn], locale='EN_US')['findings']:
        print(r['title'],r['severity'])
