#!/bin/bash

policies=$(aws iam list-policies --scope Local --query 'Policies[].[PolicyName]' --output text)

YOUR_ACCOUNT_ID=$(aws sts get-caller-identity | jq .Account)

for i in $policies
do
  echo $i 
  # aws iam get-policy --policy-arn arn:aws:iam::$YOUR_ACCOUNT_ID:policy/$i
done