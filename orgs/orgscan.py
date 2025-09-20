#!/usr/bin/env python

import boto3,json
from botocore.exceptions import ClientError

def get_all_policies(org_client) -> dict:
    policy_map = {}
    paginator = org_client.get_paginator('list_policies')

    try:
        # Use a paginator to handle large numbers of policies
        for page in paginator.paginate(Filter='SERVICE_CONTROL_POLICY'):
            for policy_summary in page['Policies']:
                policy_id = policy_summary['Id']

                policy_details = org_client.describe_policy(PolicyId=policy_id)['Policy']

                policy_map[policy_id] = {
                    'Id': policy_id,
                    'Name': policy_details['PolicySummary']['Name'],
                    'Description': policy_details['PolicySummary']['Description'],
                    'Content': policy_details['Content'] # Content is a JSON string
                }
        print(f"✅ Found {len(policy_map)} policies.")
    except ClientError as e:
        print(f"Error fetching policies: {e}")
        return {}
    return policy_map

def get_organization_structure(org_client) -> tuple[dict, dict, dict]:
    ou_map = {}
    account_map = {}
    policy_attachments = {}

    try:
        # 1. Start with the root
        root = org_client.list_roots()['Roots'][0]
        root_id = root['Id']

        # We'll treat the root like an OU for storage consistency
        ou_map[root_id] = {'Id': root_id, 'Name': 'Root', 'Arn': root['Arn'], 'ParentId': None}

        # 2. Use a list as a queue to process parents (starting with the root)
        nodes_to_visit = [root_id]

        while nodes_to_visit:
            parent_id = nodes_to_visit.pop(0)

            attached_scps = org_client.list_policies_for_target(
                TargetId=parent_id, Filter='SERVICE_CONTROL_POLICY'
            )['Policies']
            if attached_scps:
                policy_attachments[parent_id] = [p['Id'] for p in attached_scps]

            paginator_ou = org_client.get_paginator('list_organizational_units_for_parent')
            for page in paginator_ou.paginate(ParentId=parent_id):
                for ou in page['OrganizationalUnits']:
                    ou_id = ou['Id']
                    ou_map[ou_id] = {'Id': ou_id, 'Name': ou['Name'], 'Arn': ou['Arn'], 'ParentId': parent_id}
                    nodes_to_visit.append(ou_id)

            paginator_acc = org_client.get_paginator('list_accounts_for_parent')
            for page in paginator_acc.paginate(ParentId=parent_id):
                for account in page['Accounts']:
                    account_id = account['Id']
                    account_map[account_id] = {'Id': account_id, 'Name': account['Name'], 'Arn': account['Arn'], 'Email': account['Email'], 'ParentId': parent_id}

                    # Get SCPs for the account
                    acc_scps = org_client.list_policies_for_target(
                        TargetId=account_id, Filter='SERVICE_CONTROL_POLICY'
                    )['Policies']
                    if acc_scps:
                        policy_attachments[account_id] = [p['Id'] for p in acc_scps]

        print(f"✅ Mapped {len(ou_map)} OUs (including root) and {len(account_map)} accounts.")

    except ClientError as e:
        print(f"Error mapping organization: {e}")
        return {}, {}, {}

    return ou_map, account_map, policy_attachments


if __name__ == "__main__":
    try:
        organizations_client = boto3.client('organizations')
        policy_map = get_all_policies(organizations_client)
        ou_map, account_map, policy_attachments = get_organization_structure(organizations_client)


        print("\n--- Summary ---")
        print(f"Total Policies Found: {len(policy_map)}")
        print(f"Total OUs (incl. Root): {len(ou_map)}")
        print(f"Total Accounts Found: {len(account_map)}")
        print(f"Entities with SCPs Attached: {len(policy_attachments)}")

        print("\n--- Detailed Organization Units (OUs) ---")
        print(json.dumps(ou_map, indent=2))

        print("\n--- Detailed Accounts ---")
        print(json.dumps(account_map, indent=2))

        print("\n--- Detailed Policies ---")
        for policy_id, policy_details in policy_map.items():
            print(f"\n--- Policy ID: {policy_id} (Name: {policy_details.get('Name', 'N/A')}) ---")
            if 'Content' in policy_details:
                try:
                    # 'Content' is a JSON string, so we need to parse it first
                    policy_content_json = json.loads(policy_details['Content'])
                    # Then print the parsed JSON content by itself
                    print(json.dumps(policy_content_json, indent=2))
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON content for policy {policy_id}: {e}")
                    print("Raw Content (not valid JSON):")
                    print(policy_details['Content'])
            else:
                print("No 'Content' field found for this policy.")



        print("\n--- Detailed Policy Attachments ---")
        print(json.dumps(policy_attachments, indent=2))


    except Exception as e:
        print(f"An unexpected error occurred: {e}")
