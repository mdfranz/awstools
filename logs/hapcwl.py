#!/usr/bin/env python

import boto3,sys,string,time

# Filter out crap, modify for your apps
filter_string = "-js -themes -Stopping -started -OK -unavailable -backend -DOWN -aboutMe -NOSRV -login.html -SSL -Stopped"
limit=10000  # how many events to return
time_filter=250 # only return events with Tr:(Total time spent waiting for the server to send a full HTTP response. In milliseconds.

def clean_url(u):
    """Remove parameters to clean things up"""
    return u.split('?')[0]

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "./hapcwl.py <region> <days_back> <min_call_ms> [log_group] [log_stream]"
    else:
        region = sys.argv[1]

        if len(sys.argv) > 2:
            start_search = time.time() -  ( int(sys.argv[2]) * 3600 * 24 )
        else :
            start_search = time.time() - 3600 * 24

        if len(sys.argv) > 3:
            time_filter = int(sys.argv[3])

        if len(sys.argv) > 4:
            log_group = sys.argv[4]
        else:
            log_group = '/var/log/haproxy.log'

        l = boto3.client("logs",region_name = region)
        streams = []


        # Find out all the log streams in the group
        for s in l.describe_log_streams(logGroupName=log_group)['logStreams']:
            streams.append(s['logStreamName'])

        # Search through all the events   TODO - probably need to figure out how to handle more than 10000 events

        for e in l.filter_log_events(logStreamNames=streams,startTime=int(start_search*1000),logGroupName=log_group,filterPattern=filter_string,limit=limit)['events']:
            fields = e['message'].split()

            try:
                haproxy_stats = fields[9].split('/')
                http_time = int(haproxy_stats[3])
                if http_time > time_filter:
                    print http_time, e['logStreamName'], string.join(fields[0:3],' '),fields[8],clean_url(fields[18])
                #print `fields`
            except:
                print fields
                sys.exit(-1)
