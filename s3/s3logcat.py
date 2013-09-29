#!/usr/bin/env python

import boto,sys,os


print `sys.argv`

if len(sys.argv) > 1:
  prefix = ""
else:
  prefix = sys.argv[1]

if len(sys.argv) > 2:
  key_match = sys.argv[2]
else:
  key_match = ""

if os.environ.has_key("LOGBUCKET"):
  s3 = boto.connect_s3()
  bucket = s3.get_bucket(os.environ["LOGBUCKET"])

  for k in bucket.list(prefix):
    if key_match != "":
      if k.name.find(key_match) > -1:
        print k.get_contents_as_string()
    else:
        print k.get_contents_as_string()

else:
  print "set LOGBUCKET to a bucket name"
  print "Usage:"
  print "\ts3logcat.py [prefix] [datestring]"
  print "\t Examples: s3logcat.py logs 2013-09-29"
