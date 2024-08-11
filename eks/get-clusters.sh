#!/bin/bash

regions=$(aws ec2 describe-regions --query 'Regions[*].RegionName' --output text)

for region in $regions
do
  echo "=== $region"
  aws --region $region eks list-clusters
  aws ec2 describe-instances --region $region --filters Name=instance-state-name,Values=running --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,PublicDnsName,State.Name]' --output table
done
