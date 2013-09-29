#!/usr/bin/env python

import boto,sys,os

if len(sys.argv) == 1:
  prefix = ""
else:
  prefix = sys.argv[1]

if os.environ.has_key("LOGBUCKET"):
  s3 = boto.connect_s3()
  bucket = s3.get_bucket(os.environ["LOGBUCKET"])

  for k in bucket.list(prefix):
    print k.get_contents_as_string()

else:
  print "set LOGBUCKET to a bucket name"
  print "Usage:"
  print "\ts3logcat.py [prefix]"
