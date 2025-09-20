#!/usr/bin/env python

import boto3,json
from botocore.exceptions import ClientError
from datetime import datetime

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

def generate_markdown_report(ou_map, account_map, policy_attachments, policy_map, output_file="aws_organization_report.md"):
    try:
        with open(output_file, 'w') as f:
            # Header and metadata
            f.write("# AWS Organization Structure Report\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Summary section
            f.write("## Summary\n\n")
            f.write(f"- **Total Organizational Units (including Root):** {len(ou_map)}\n")
            f.write(f"- **Total Accounts:** {len(account_map)}\n")
            f.write(f"- **Total Service Control Policies:** {len(policy_map)}\n")
            f.write(f"- **Entities with SCPs Attached:** {len(policy_attachments)}\n\n")

            # Organization Units section
            f.write("## Organizational Units\n\n")
            f.write("| OU ID | Name | Parent ID | ARN |\n")
            f.write("|-------|------|-----------|-----|\n")

            for ou_id, ou_details in ou_map.items():
                parent_name = "N/A" if ou_details['ParentId'] is None else ou_map.get(ou_details['ParentId'], {}).get('Name', ou_details['ParentId'])
                f.write(f"| `{ou_id}` | {ou_details['Name']} | {parent_name} | `{ou_details['Arn']}` |\n")

            f.write("\n")

            # Accounts section
            f.write("## Accounts\n\n")
            f.write("| Account ID | Name | Email | Parent OU | ARN |\n")
            f.write("|------------|------|-------|-----------|-----|\n")

            for account_id, account_details in account_map.items():
                parent_name = ou_map.get(account_details['ParentId'], {}).get('Name', account_details['ParentId'])
                f.write(f"| `{account_id}` | {account_details['Name']} | {account_details['Email']} | {parent_name} | `{account_details['Arn']}` |\n")

            f.write("\n")

            # Policy Attachments section
            f.write("## Policy Attachments\n\n")
            if policy_attachments:
                f.write("### Entities with Service Control Policies\n\n")
                for target_id, policy_ids in policy_attachments.items():
                    # Determine if target is an OU or Account
                    if target_id in ou_map:
                        target_type = "OU"
                        target_name = ou_map[target_id]['Name']
                    elif target_id in account_map:
                        target_type = "Account"
                        target_name = account_map[target_id]['Name']
                    else:
                        target_type = "Unknown"
                        target_name = "Unknown"

                    f.write(f"#### {target_type}: {target_name} (`{target_id}`)\n\n")
                    f.write("**Attached Policies:**\n")
                    for policy_id in policy_ids:
                        policy_name = policy_map.get(policy_id, {}).get('Name', 'Unknown Policy')
                        f.write(f"- `{policy_id}` - {policy_name}\n")
                    f.write("\n")
            else:
                f.write("No Service Control Policies are currently attached to any entities.\n\n")

            # Service Control Policies section
            f.write("## Service Control Policies\n\n")
            if policy_map:
                for policy_id, policy_details in policy_map.items():
                    f.write(f"### {policy_details['Name']} (`{policy_id}`)\n\n")
                    f.write(f"**Description:** {policy_details.get('Description', 'No description available')}\n\n")

                    # Show where this policy is attached
                    attached_to = []
                    for target_id, policy_ids in policy_attachments.items():
                        if policy_id in policy_ids:
                            if target_id in ou_map:
                                attached_to.append(f"OU: {ou_map[target_id]['Name']} (`{target_id}`)")
                            elif target_id in account_map:
                                attached_to.append(f"Account: {account_map[target_id]['Name']} (`{target_id}`)")

                    if attached_to:
                        f.write("**Attached to:**\n")
                        for attachment in attached_to:
                            f.write(f"- {attachment}\n")
                        f.write("\n")
                    else:
                        f.write("**Attached to:** Not currently attached to any entities\n\n")

                    # Policy content
                    f.write("**Policy Document:**\n")
                    f.write("```json\n")
                    try:
                        policy_content = json.loads(policy_details['Content'])
                        f.write(json.dumps(policy_content, indent=2))
                    except json.JSONDecodeError:
                        f.write(policy_details['Content'])
                    f.write("\n```\n\n")
            else:
                f.write("No Service Control Policies found.\n\n")

            # Organization Hierarchy section
            f.write("## Organization Hierarchy\n\n")
            f.write("This section shows the hierarchical structure of your AWS Organization.\n\n")

            def write_hierarchy(parent_id, indent=0):
                indent_str = "  " * indent

                # Write OUs under this parent
                for ou_id, ou_details in ou_map.items():
                    if ou_details['ParentId'] == parent_id:
                        policies_text = ""
                        if ou_id in policy_attachments:
                            policy_names = [policy_map.get(pid, {}).get('Name', pid) for pid in policy_attachments[ou_id]]
                            policies_text = f" 🔒 SCPs: {', '.join(policy_names)}"

                        f.write(f"{indent_str}- **{ou_details['Name']}** (`{ou_id}`){policies_text}\n")
                        write_hierarchy(ou_id, indent + 1)

                # Write Accounts under this parent
                for account_id, account_details in account_map.items():
                    if account_details['ParentId'] == parent_id:
                        policies_text = ""
                        if account_id in policy_attachments:
                            policy_names = [policy_map.get(pid, {}).get('Name', pid) for pid in policy_attachments[account_id]]
                            policies_text = f" 🔒 SCPs: {', '.join(policy_names)}"

                        f.write(f"{indent_str}  - 🏢 **{account_details['Name']}** (`{account_id}`) - {account_details['Email']}{policies_text}\n")

            # Start from root
            root_id = None
            for ou_id, ou_details in ou_map.items():
                if ou_details['ParentId'] is None:
                    root_id = ou_id
                    break

            if root_id:
                write_hierarchy(root_id)

            f.write("\n---\n")
            f.write("*Report generated by AWS Organizations Scanner*\n")

        print(f"✅ Markdown report generated: {output_file}")
        return output_file

    except Exception as e:
        print(f"Error generating Markdown report: {e}")
        return None

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

        print("\n--- Creating Markdown Document ---")
        generate_markdown_report(ou_map, account_map, policy_attachments, policy_map)


    except Exception as e:
        print(f"An unexpected error occurred: {e}")
