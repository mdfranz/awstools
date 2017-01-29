#!/usr/bin/env python

import boto3,sys,string,time,socket


# Filter out crap, modify for your apps
filter_string = "-js -themes -Stopping -started -OK -unavailable -backend -DOWN -aboutMe -NOSRV -login.html -SSL -Stopped"
limit=10000  # how many events to return
time_filter=250 # only return events with Tr:(Total time spent waiting for the server to send a full HTTP response. In milliseconds.
log_group = '/var/log/haproxy.log'  # default log group

# Set carbon_host to None to disable
#carbon_host="10.12.5.200"
carbon_host=None
carbon_port=2003

def send_metric(s):
    """Sends a metric to an open socket"""
    pass

def clean_url(u):
    """Remove parameters to clean things up"""
    return u.split('?')[0].replace('/','_').replace('.','_')

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

        l = boto3.client("logs",region_name = region)
        streams = []

        if carbon_host:
            carbon = socket.socket()
            carbon.connect((carbon_host, carbon_port))

        # Go through log streams
        for s in l.describe_log_streams(logGroupName=log_group)['logStreams']:
            print "------> Searching",s
            for e in l.filter_log_events(logStreamNames=[s['logStreamName']],startTime=int(start_search*1000),logGroupName=log_group,filterPattern=filter_string,limit=limit)['events']:
                epoch = int(e['timestamp']) / 1000
                fields = e['message'].split()
                try:
                    haproxy_stats = fields[9].split('/')
                    http_time = int(haproxy_stats[3])
                    service = fields[8].split('/')[0]
                    url = clean_url(fields[18])
                    if http_time > time_filter:
                        if carbon_host:
                            """print "> Timestamp",epoch
                            print "> Host",e['logStreamName']
                            print "> Service",service
                            print "> Url", url
                            print "> Duration",http_time"""
                            message = '%s.%s.%s %d %d\n' % ( e['logStreamName'], service, url, http_time, epoch )
                            print "Sending:",  message
                            carbon.sendall(message)
                        else:
                            print http_time, e['logStreamName'], string.join(fields[0:3],' '),fields[8],url
                        

                except Exception as e:
                    # Dump the event and stop if you can't parse properly
                    print "Error",e
                    print fields
                    sys.exit(-1)
