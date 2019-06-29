#!/usr/bin/env python

import boto3,sys,string,time,socket

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "./clean_logs.py <region>"
    else:
        region = sys.argv[1]
        c = boto3.client("logs",region_name = region)

        for g in c.describe_log_groups()['logGroups']:
            log_group = g['logGroupName']

            print "GROUP",log_group

            if int(g['storedBytes']) == 0:
                print "EMPTY LOG GROUP, DELETING"
                c.delete_log_group(logGroupName=log_group)
                continue 

            for s in c.describe_log_streams(logGroupName=log_group)['logStreams']:
                print  s
