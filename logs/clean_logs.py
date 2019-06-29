#!/usr/bin/env python

stream_delete = 180 # delete log streams if last ingest time greater than 180 

import boto3,sys,string,time,socket

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "./clean_logs.py <region>"
    else:
        region = sys.argv[1]
        c = boto3.client("logs",region_name = region)

        for g in c.describe_log_groups()['logGroups']:
            log_group = g['logGroupName']
            stream_count = len ( c.describe_log_streams(logGroupName=log_group)['logStreams'] )

            print "FOUND GROUP",log_group, g['storedBytes'], stream_count

            if int(g['storedBytes']) == 0 or stream_count == 0:
                print "EMPTY LOG GROUP, DELETING:",log_group
                c.delete_log_group(logGroupName=log_group)
                continue 

            for s in c.describe_log_streams(logGroupName=log_group)['logStreams']:
                log_stream = s['logStreamName']
                age_sec = int(time.time()) -  ( s['lastIngestionTime'] / 1000 ) 

                print "FOUND STREAM", log_stream, s['lastIngestionTime']

                if ( age_sec / ( 3600 * 24 ) )  > 180: 
                    print s 
                    print "STALE LOG STREAM, DELETING:",log_stream
                    r = c.delete_log_stream(logGroupName=log_group,logStreamName=log_stream)
                    print r
