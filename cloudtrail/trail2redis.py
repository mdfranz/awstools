#!/usr/bin/env python3

import json,redis,sys

r = redis.Redis()

with open(sys.argv[1]) as f:
  j = json.load(f)
  for m in j['Records']:
    r.lpush("cloudtrail",json.dumps(m))
