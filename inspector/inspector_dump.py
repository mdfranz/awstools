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
  print ("\n== Getting findings ==")
  for f in p.paginate():
    for arn in f['findingArns']:
      print()
      print (arn)
      for r in c.describe_findings(findingArns=[arn], locale='EN_US')['findings']:
        print(r['title'],r['severity'])

  print ("\n== Getting asessment runs ==")
  p = c.get_paginator("list_assessment_runs")
  for r in p.paginate():
    for arn in r['assessmentRunArns']:
      print (arn)


  p = c.get_paginator("list_assessment_targets")
  print ("\n== Getting targets ==")
  for t in p.paginate():
    for arn in t['assessmentTargetArns']:
      print(arn)


