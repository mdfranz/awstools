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

metric_config = {}
metric_config["AWS/RDS"] = {
  "dimension": "DBInstanceIdentifier",
  "metrics": { 
    "NetworkTransmitThroughput": ["Average","Bytes"],
    "NetworkReceiveThroughput": ["Average","Bytes"],
    "ReadLatency": ["Average","Seconds"],
    "WriteLatency": ["Average","Seconds"],
    "ReadIOPS": ["Average","Count/Second"],
    "WriteIOPS": ["Average","Count/Second"],
    "DatabaseConnections": ["Average","Count"],
    "CPUUtilization": ["Average","Percent"],
    "DiskQueueDepth": ["Average","Count"]
  }
}

metric_config["AWS/ELB"] = {
  "dimension": "LoadBalancerName",
  "metrics": {
    "SurgeLength": [],
    "Latency": [],
    "RequestCount": [],
  }  
}

def dumpe_metric(m,debug=True):
  """Extract the goodies"""
  m_hash = {}
  if debug:
    print "Name:",m.name
    print "Namespace: ",m.namespace
    print "Dimensions:",
  for d in m.dimensions.keys():
    for v in m.dimensions[d]:
      if debug:
        print d,v

c = boto.ec2.cloudwatch.connect_to_region(sys.argv[1])

# This will become the metrics.json
cwatch_config = {}
cwatch_config["carbonNameSpacePrefix"] = "cloudwatch" + "-" + sys.argv[1]
cwatch_config["numberOfOverlappingPoints"] = 2
cwatch_config["metrics"] = []

# Dump all the metrics for a given region
for m in c.list_metrics():
  metric = {}

  # Skip AWS resources we don't care about
  if m.namespace in metric_config.keys():
    for d in m.dimensions.keys():
      if d == metric_config[m.namespace]["dimension"]:
        if m.name in metric_config[m.namespace]["metrics"].keys():
          if len(metric_config[m.namespace]["metrics"][m.name]) > 0:
            metric["Namespace"] = m.namespace
            metric["MetricName"] = m.name
            metric["Dimensions.member.1.Name"] = d
            metric["Dimensions.member.1.Value"] = m.dimensions[d][0]
            metric["Unit"] = metric_config[m.namespace]["metrics"][m.name][1]
            metric["Statistics.member.1"] = metric_config[m.namespace]["metrics"][m.name][0]
  if metric != {}:
    cwatch_config["metrics"].append(metric)

print json.dumps(cwatch_config,indent=4, separators=(',', ': '))
