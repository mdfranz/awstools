import boto3

c = boto3.client("s3")
r = boto3.resource("s3")

for b in c.list_buckets()['Buckets']:  
    print "\n\n- BUCKET:", b['Name']
    br = r.Bucket(b['Name'])

    b_logging = br.Logging()
    print "- LOGGING:",b_logging.logging_enabled

    b_acl = br.Acl()
    print "- ACL:",b_acl.grants

    b_tags = br.Tagging()
    try:
        print "- TAGS:",b_tags.tag_set
    except:
        pass
