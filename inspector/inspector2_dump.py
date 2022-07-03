#!/usr/bin/env python3

# See https://github.com/grepcoffee/aws-scripts/blob/master/inspector/ListFindingsBySev/listfindings.py

import boto3,sys

if __name__ == "__main__":
  if len(sys.argv) > 1:
    my_region = sys.argv[1]
  else:
    my_region = "us-east-1"

  c = boto3.client("inspector2",region_name=my_region)

  p = c.get_paginator("list_findings")
  print ("\n== Getting findings ==")
  for f in p.paginate():
    for fi in (f['findings']):
      print("\n====",fi['findingArn'])
      print (fi['description'])
