#!/bin/bash

#
# based on https://medium.com/@joachim8675309/eks-ebs-storage-with-eksctl-3e526f534215
#

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <region> <cluster_name>"
    exit 1
fi

EKS_REGION="$1"
EKS_CLUSTER_NAME="$2"

echo "=== Checking EBS CSI Addon"
eksctl get addon \
  --name "aws-ebs-csi-driver" \
  --region $EKS_REGION \
  --cluster $EKS_CLUSTER_NAME
echo 

eksctl get iamserviceaccount --region $EKS_REGION --cluster $EKS_CLUSTER_NAME 


kubectl get sa ebs-csi-controller-sa -n kube-system -o yaml 

echo "=== Nodes and Pods"

kubectl get nodes
kubectl get pods -A -o wide 
kubectl get deployment ebs-csi-controller -n kube-system
echo 

echo "=== Displaying addons"
eksctl get addons --region $EKS_REGION --cluster $EKS_CLUSTER_NAME
