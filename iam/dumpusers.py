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

    policy_response = iam_conn.get_all_user_policies(u['user_name'])
    policy_results = policy_response['list_user_policies_response']
    policies = policy_results['list_user_policies_result']

    #print policies['policy_names']

    if len(policies['policy_names']) > 0:
        for policy_name in policies['policy_names']:
            #print "Checking", policy_name

            user_policy_response = iam_conn.get_user_policy(u['user_name'],policy_name)
            user_policy_dict = user_policy_response['get_user_policy_response']
            user_policy_result = user_policy_dict['get_user_policy_result']
            policy_doc = user_policy_result['policy_document']

            policy_json = json.loads(urllib.unquote(policy_doc))
            policy_statement = policy_json['Statement'][0]

            if policy_statement.has_key('Action'):
              policy_action = policy_statement['Action']
              policy_resource = policy_statement['Resource']

              if isinstance(policy_resource,list):
                  for r in policy_resource:
                      if r.find(service) > -1:
                          print "[- %s %s -]"  % (u['user_name'], u['user_id'])
                          print r
              else:
                  for r in policy_resource:
                      if r.find(service) > -1:
                          print "[- %s %s -]"  % (u['user_name'], u['user_id'])
                          print r
