#!/usr/bin/env python

import boto.iam,sys,urllib,json

if len(sys.argv) == 2:
    service = sys.argv[1]
else:
    service = "arn"

iam_conn = boto.connect_iam()

user_response = iam_conn.get_all_users()
list_users =  user_response['list_users_response']
user_results =  list_users['list_users_result']
users = user_results['users']
for u in  users:
    access_keys_response = iam_conn.get_all_access_keys(u['user_name'])
    list_access_keys = access_keys_response['list_access_keys_response']
    results = list_access_keys['list_access_keys_result']
    for k in results['access_key_metadata']:
      print k

