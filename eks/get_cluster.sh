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

echo "=== Dumping IAM Service Accounts"
eksctl get iamserviceaccount --region $EKS_REGION --cluster $EKS_CLUSTER_NAME 

kubectl get sa ebs-csi-controller-sa -n kube-system -o yaml 
kubectl get sa aws-load-balancer-controller -n kube-system -o yaml 

echo 
echo "=== Showing nodes, pods, and deployments"

kubectl get nodes
kubectl get pods -A -o wide 

echo
kubectl get deployment -n kube-system
echo 

echo "=== Displaying addons"
eksctl get addons --region $EKS_REGION --cluster $EKS_CLUSTER_NAME -o yaml
