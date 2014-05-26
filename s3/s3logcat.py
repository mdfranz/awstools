#!/usr/bin/env python

import boto,sys,os,string

def usage():
  print "set LOGBUCKET to a bucket name"
  print "Usage:"
  print "\ts3logcat.py [prefix] [datestring]"
  print "\t Examples: s3logcat.py logs 2013-09-29"

if len(sys.argv) == 1:
  usage()
  sys.exit()

if len(sys.argv) > 1 :
  prefix = sys.argv[1]

if len(sys.argv) > 2:
  key_match = sys.argv[2]
else:
  key_match = ""


print "Prefix %s Match: %s" % (prefix,key_match)

if os.environ.has_key("LOGBUCKET"):
  s3 = boto.connect_s3()
  bucket = s3.get_bucket(os.environ["LOGBUCKET"])
  print "Using bucket: %s" % bucket.name

  for k in bucket.list(prefix):
    if key_match == ""  or k.name.find(key_match) > 0:
      l =  k.get_contents_as_string().rstrip()
      parsed = l.split()

      print parsed[2]+parsed[3], parsed[4], parsed[5], parsed[7]
