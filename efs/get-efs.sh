#!/bin/bash

# Check if the argument is passed
if [ $# -eq 0 ]; then
    echo "No arguments provided"
    echo "Usage: ./script-name <aws-region>"
    exit 1
fi

# Take AWS region as an argument
region=$1

# Get the EFS filesystem ID. You can modify this to take the ID as an argument.
filesystem_id=$(aws efs describe-file-systems --region $region --query 'FileSystems[*].FileSystemId' --output text)

if [ -z "$filesystem_id" ]; then
    echo "No Filesystem found"
    exit 1
else
    # Describe the EFS filesystem
    aws efs describe-file-systems \
        --region $region \
        --file-system-id "$filesystem_id" \
        --query 'FileSystems[*]' \
        --output table

    # Describe the mount targets for the EFS filesystem
    aws efs describe-mount-targets \
        --region $region \
        --file-system-id "$filesystem_id" \
        --query 'MountTargets[*]' \
        --output table
fi
