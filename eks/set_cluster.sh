#!/bin/bash

#

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <region> <cluster_name>"
    exit 1
fi

EKS_REGION="$1"
EKS_CLUSTER_NAME="$2"

aws eks --region $EKS_REGION update-kubeconfig --name $EKS_CLUSTER_NAME
kubectl get nodes
kubectl cluster-info
