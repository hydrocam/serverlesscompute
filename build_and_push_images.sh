#!/bin/bash

# Configuration
AWS_REGION="us-west-1"
ACCOUNT_ID="767121720320"
REPO_NAME="simulationsitesrepository"
ECR_URL="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME"

# Create ECR repo (if not exists)
aws ecr create-repository --repository-name $REPO_NAME --region $AWS_REGION 2>/dev/null

# Authenticate Docker with ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL

# Loop through site1 to site100
for i in $(seq 138 138); do
    TAG="site${i}-containerimage"
    MODEL_NAME="site${i}_checkpoint.pth"
    MODEL_DIR="model"

    echo "🚀 Building image $TAG using model file: $MODEL_NAME"

    # Rename the model file for this site
    mv "$MODEL_DIR/model_checkpoint.pth" "$MODEL_DIR/$MODEL_NAME"

    # Update config.py with site-specific path
    sed -i.bak "s|checkpoint_path *= *[\"'].*[\"']|checkpoint_path = \"/var/task/model/$MODEL_NAME\"|" src/config.py

    # Build Docker image
    docker build -t $TAG .

    # Tag and push to ECR
    docker tag $TAG $ECR_URL:$TAG
    docker push $ECR_URL:$TAG

    echo "✅ Pushed: $ECR_URL:$TAG"

    # Restore original model filename for next loop
    mv "$MODEL_DIR/$MODEL_NAME" "$MODEL_DIR/model_checkpoint.pth"
done

echo "🎉 All 100 images successfully built and pushed to $ECR_URL"
