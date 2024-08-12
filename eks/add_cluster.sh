#!/bin/bash

#
# based on https://medium.com/@joachim8675309/eks-ebs-storage-with-eksctl-3e526f534215
#

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <region> <cluster_name> <instance_type>"
    exit 1
fi

EKS_REGION="$1"
EKS_CLUSTER_NAME="$2"
EKS_VERSION="1.29"
INSTANCE_TYPE="$3"

ACCOUNT_ID=$(aws sts get-caller-identity \
  --query "Account" \
  --output text
)

KUBECONFIG=$HOME/.kube/$ACCOUNT_ID-$EKS_REGION-$EKS_CLUSTER_NAME.yaml

echo "KUBECONFIG: $KUBECONFIG"

eksctl create cluster \
  --region $EKS_REGION \
  --name $EKS_CLUSTER_NAME \
  --version $EKS_VERSION \
  --node-type $INSTANCE_TYPE \
  --nodes-min=2 --nodes-max=5
 
ROLE_NAME="eksctl-${EKS_CLUSTER_NAME}_EBS_CSI_DriverRole"
ACCOUNT_ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"

#
# TODO - should check for existing Association 
#

eksctl utils associate-iam-oidc-provider \
  --cluster $EKS_CLUSTER_NAME \
  --region $EKS_REGION \
  --approve

POLICY_ARN="arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"

eksctl create iamserviceaccount \
  --name "ebs-csi-controller-sa" \
  --namespace "kube-system" \
  --cluster $EKS_CLUSTER_NAME \
  --region $EKS_REGION \
  --attach-policy-arn $POLICY_ARN \
  --role-only \
  --role-name $ROLE_NAME \
  --approve

eksctl create addon \
  --name "aws-ebs-csi-driver" \
  --cluster $EKS_CLUSTER_NAME \
  --region=$EKS_REGION \
  --service-account-role-arn $ACCOUNT_ROLE_ARN \
  --force

echo "Deploying Metrics Server"

kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

echo "Checking EBS CSI Addon"

eksctl get addon \
  --name "aws-ebs-csi-driver" \
  --region $EKS_REGION \
  --cluster $EKS_CLUSTER_NAME

echo "Checking Service Account"

kubectl get sa ebs-csi-controller-sa -n kube-system -o yaml 
eksctl get iamserviceaccount --region $EKS_REGION --cluster $EKS_CLUSTER_NAME -

echo "Restarting EBS CSI Controller"
kubectl rollout restart deployment ebs-csi-controller -n kube-system

sleep 3 

kubectl get nodes
kubectl get pods -A -o wide 

kubectl get deployment ebs-csi-controller -n kube-system
eksctl get addons --region $EKS_REGION --cluster $EKS_CLUSTER_NAME
