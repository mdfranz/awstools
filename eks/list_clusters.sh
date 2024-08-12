#!/bin/bash

if [ "$#" -eq 0 ]; then
  regions=$(aws ec2 describe-regions --query 'Regions[*].RegionName' --output text)
else
  regions=$1
fi

for region in $regions
do
  echo "=== $region"
  aws --region $region eks list-clusters
  aws ec2 describe-instances --region $region --filters Name=instance-state-name,Values=running --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,PublicDnsName,State.Name]' --output table
done
