#!/usr/bin/env python


"""
Create these files:

https://github.com/edasque/cloudwatch2graphite/blob/master/conf/metrics.json.sample


{
    "metrics": [
            {
                    "Namespace": "AWS/RDS",
                    "MetricName": "CPUUtilization",
                    "Statistics.member.1": "Average",
                    "Unit": "Percent",
                    "Dimensions.member.1.Name":"DBInstanceIdentifier",
                    "Dimensions.member.1.Value":"my_instance"
            }
              ],
                "carbonNameSpacePrefix" : "cloudwatch",
                "numberOfOverlappingPoints" : 2
}
"""

import boto.ec2.cloudwatch,sys,json

c = boto.ec2.cloudwatch.connect_to_region(sys.argv[1])
cwatch_config = {}
cwatch_config["carbonNameSpacePrefix"] = "cloudwatch"
cwatch_config["numberOfOverlappingPoints"] = 2
cwatch_config["metrics"] = []

for m in c.list_metrics():
  metric = {}
  if m.namespace == "AWS/RDS":
    if m.dimensions.has_key("DBInstanceIdentifier"):
        metric["Namespace"] = m.namespace
        metric["MetricName"] = "CPUUtilization"
        metric["Unit"] = "Percent"
        metric["Dimensions.member.1.Name"] = "DBInstanceIdentifier"
        metric["Statistics.member.1"] = "Average"
        metric["Dimensions.member.1.Value"] = m.dimensions["DBInstanceIdentifier"][0]
  if metric != {}:
    cwatch_config["metrics"].append(metric)

print json.dumps(cwatch_config,indent=4, separators=(',', ': '))
