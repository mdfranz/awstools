#!/bin/bash

#
# Originally based on https://medium.com/@joachim8675309/eks-ebs-storage-with-eksctl-3e526f534215
#

METRICS_CRD="https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"
CERTMGR_CRD="https://github.com/jetstack/cert-manager/releases/download/v1.12.3/cert-manager.yaml"
LBC_CRD="https://github.com/kubernetes-sigs/aws-load-balancer-controller/releases/download/v2.8.2/v2_8_2_full.yaml"

#
#
#

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <region> <cluster_name> <instance_type>"
    exit 1
fi

#
#
#

EKS_REGION="$1"
EKS_CLUSTER_NAME="$2"
EKS_VERSION="1.29"
INSTANCE_TYPE="$3"

ACCOUNT_ID=$(aws sts get-caller-identity  --query "Account" --output text)
KUBECONFIG=$HOME/.kube/$ACCOUNT_ID-$EKS_REGION-$EKS_CLUSTER_NAME.yaml

# CSI_ROLE_NAME="eksctl-${EKS_CLUSTER_NAME}_EBS_CSI_DriverRole"
# ACCOUNT_ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$CSI_ROLE_NAME"

view_cluster() {
  echo "=== Checking EBS CSI Addon"
  eksctl get addon \
    --name "aws-ebs-csi-driver" \
    --region $EKS_REGION \
    --cluster $EKS_CLUSTER_NAME

  echo "=== Checking Service Account"
  kubectl get sa ebs-csi-controller-sa -n kube-system -o yaml 
  eksctl get iamserviceaccount --region $EKS_REGION --cluster $EKS_CLUSTER_NAME -

  kubectl get nodes
  kubectl get pods -A -o wide 
  kubectl get deployment ebs-csi-controller -n kube-system

  echo "=== Displaying addons"
  eksctl get addons --region $EKS_REGION --cluster $EKS_CLUSTER_NAME
}

read -p "Enable strict mode? (y/N) " exiterror
if [[ $exiterror =~ ^[Yy]$ ]]
then
  set -euo pipefail
fi 

echo "Creating cluster $EKS_CLUSTER_NAME in $ACCOUNT_ID in $EKS_REGION"

# eksctl create cluster \
#  --region $EKS_REGION  --name $EKS_CLUSTER_NAME \
#  --version $EKS_VERSION \
#  --node-type $INSTANCE_TYPE  --nodes-min=2 --nodes-max=5 --dumpLogs
 
tempfile=$(mktemp)

echo "=== Generating YAML eksctl configuration"
echo "YAML configuration for Cluster will be in $tempfile"

cat << EOF > $tempfile
---
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: ${EKS_CLUSTER_NAME}
  region: ${EKS_REGION}
  version: "${EKS_VERSION}"

iam:
  withOIDC: true
  serviceAccounts:
  - metadata:
      name: aws-load-balancer-controller
      namespace: kube-system
    wellKnownPolicies:
      awsLoadBalancerController: true
  - metadata:
      name: ebs-csi-controller-sa
      namespace: kube-system
    wellKnownPolicies:
      ebsCSIController: true
  - metadata:
      name: external-dns
      namespace: kube-system
    wellKnownPolicies:
      externalDNS: true
  - metadata:
      name: cert-manager
      namespace: cert-manager
    wellKnownPolicies:
      certManager: true
nodeGroups:
  - name: ng-1
    instanceType: ${INSTANCE_TYPE}
    desiredCapacity: 2
    minSize: 2
    maxSize: 5
    volumeSize: 100
    volumeType: gp3
    volumeEncrypted: true
EOF

eksctl create cluster -f $tempfile

#
# TODO - should check for existing Association 
#
# eksctl utils associate-iam-oidc-provider \
#  --cluster $EKS_CLUSTER_NAME \
#  --region $EKS_REGION \
#  --approve --dumpLogs
#echo "=== Creating Service Account for EBS CSI Driver"
#POLICY_ARN="arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
#eksctl create iamserviceaccount \
#  --name "ebs-csi-controller-sa" \
#  --namespace "kube-system" \
#  --cluster $EKS_CLUSTER_NAME \
#  --region $EKS_REGION \
#  --attach-policy-arn $POLICY_ARN \
#  --role-only \
#  --role-name $CSI_ROLE_NAME \
#  --approve --dumpLogs
# eksctl create iamserviceaccount --cluster=<clusterName> --name=<serviceAccountName> --namespace=<serviceAccountNamespace> --attach-policy-arn=<policyARN>

CSI_ACCOUNT_ROLE_ARN=$(eksctl get addon --cluster  $EKS_CLUSTER_NAME --region $EKS_REGION -1 -o json | jq -r '.[]|select(.Name=="aws-ebs-csi-driver")|.IAMRole')

echo "=== Creating EBS CSI Driver Addon"
eksctl create addon \
  --name "aws-ebs-csi-driver" \
  --cluster $EKS_CLUSTER_NAME \
  --region=$EKS_REGION \
  --service-account-role-arn $CSI_ACCOUNT_ROLE_ARN \
  --force --dumpLogs

read -p "Do you want to add a metrics server? (y/N) " addMetrics
if [[ $addMetrics =~ ^[Yy]$ ]]
then
    echo "Deploying Latest Metrics Server"
    kubectl apply -f $METRICS_CRD
    sleep 3
else
    echo "Skipping Metrics Server deployment"
fi

#eksctl create iamserviceaccount \
#      --namespace "kube-system" \
#      --cluster $EKS_CLUSTER_NAME \
#      --region $EKS_REGION \
#      --name "aws-load-balancer-controller" \
#      --attach-policy-arn=arn:aws:iam::$ACCOUNT_ID:policy/LoadBalancerControllerPolicy \
#      --override-existing-serviceaccounts \
#      --approve --dumpLogs

exit 

helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
     -n kube-system --set clusterName=$EKS_CLUSTER_NAME \
     --set serviceAccount.create=false --set serviceAccount.name=aws-load-balancer-controller

kubectl apply --validate=false -f $CERTMGR_CRD

echo "=== Restarting Controllers"
echo "Restarting EBS CSI Controller"
kubectl rollout restart deployment ebs-csi-controller -n kube-system

# echo "Restarting AWS LB Controller"
# kubectl rollout restart deployment aws-load-balancer-controller -n kube-system

sleep 3

view_cluster

echo "KUBECONFIG=$KUBECONFIG"
