#!/bin/bash

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <region> <cluster_name>"
    exit 1
fi

EKS_REGION="$1"
EKS_CLUSTER_NAME="$2"

aws eks --region $EKS_REGION update-kubeconfig --name $EKS_CLUSTER_NAME

if [ $? -ne 0 ]; then
    echo "Failed to update kubeconfig for EKS Cluster $EKS_CLUSTER_NAME in region $EKS_REGION"
    exit 1
fi



kubectl get nodes
kubectl cluster-info
