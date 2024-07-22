AWS_REGIONS=$(aws ec2 describe-regions --query "Regions[*].RegionName" --output text)

# Iterate over each region
for REGION in $AWS_REGIONS; do
  echo "= Checking $REGION"
  aws workspaces describe-workspace-directories --region $REGION
done
