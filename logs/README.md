
# About
This is a quick hack to search back through your haproxy logs stored in CloudWatch logs and extract a minimal set of information that can be used to sort from command line to look for slow calls

Assumes you have AWS credentials defined somewhere in a standard boto way and boto3 is installed.

Tested on Boto3 1.3.1

# Usage
```
mfranz@mfranz-e4200:~/awstools/logs$ ./hapcwl.py 
./hapcwl.py <region> <days_back> <min_call_ms> [log_group] [log_stream]

```

# References
- https://logmatic.io/blog/haproxy-log-what-should-i-do-with-my-haproxy-logs/
- http://boto3.readthedocs.io/en/latest/reference/services/logs.html#CloudWatchLogs.Client.filter_log_events
