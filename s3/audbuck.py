#!/usr/bin/env python

import sys,os,pycurl
from boto.s3.connection import S3Connection 

aws_keys = []
urls = []
preauth_response = {}

# (username,keyid,secret)

if __name__ == "__main__":
    print `sys.argv`
    if sys.argv[1] == "crawl":
        if len(sys.argv) > 2: 
            # Read in keys from a .csv
            pass
        else:
            aws_keys.append( (None,os.environ['AWS_ACCESS_KEY_ID'],
                            os.environ['AWS_SECRET_ACCESS_KEY']) )

        for k in aws_keys:
            c = S3Connection(k[1],k[2])
            server = c.host
            
            for b in c.get_all_buckets():
                print b.name
                for f in b.get_all_keys():
                    print "- %s" % f.name
                    url = "http://%s/%s/%s" % (server,b.name,f.name)
                    urls.append(url.rstrip())

        for u in urls:
            pc = pycurl.Curl()
            pc.setopt(pycurl.URL,str(u))
            pc.perform()
            code = pc.getinfo(pycurl.HTTP_CODE)
            preauth_response[u] = code

        print `preauth_response`
