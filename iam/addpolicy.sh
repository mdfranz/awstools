#!/bin/bash

# Check if arguments are provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <policy.json>"
    exit 1
fi

POLICY_NAME=$(basename $1 .json)
POLICY_FILE=$1 

# get policy details
POLICY_DETAILS=$(aws iam get-policy --policy-arn arn:aws:iam::$(aws sts get-caller-identity --output text --query 'Account'):policy/$POLICY_NAME) 

# check if policy exists
if [[ $POLICY_DETAILS == *"An error occurred"* ]]; then
  # policy does not exists, create it
  aws iam create-policy --policy-name "$POLICY_NAME" --policy-document file://$POLICY_FILE --description "eksctl policy" 
else
  # policy exists, create a new version
  POLICY_ARN=$(echo $POLICY_DETAILS | jq -r '.Policy.Arn') 
  aws iam create-policy-version --policy-arn "$POLICY_ARN" --policy-document file://$POLICY_FILE --set-as-default
fi

