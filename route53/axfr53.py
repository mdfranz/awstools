#!/usr/bin/env python

# assumes ROUTE53_ZONEID is set and normal boto vars

import boto,os

r = boto.connect_route53()

if os.environ['ROUTE53_ZONEID'] != "":
  records = r.get_all_rrsets(os.environ['ROUTE53_ZONEID'])
  for a in records:
    if a.type =="A":
      print a.name.rstrip('.')
else:
  print "set ROUTE53_ZONEID with your hosted zone ID"

