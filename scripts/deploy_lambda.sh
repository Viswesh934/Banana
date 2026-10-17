#!/usr/bin/env bash
# ==============================================================================
# 🍌 Banana Serverless Lambda Deployment Script
# Deploys Banana Graph Context Brain to AWS Lambda backed by FalkorDB Cloud
# ==============================================================================

set -euo pipefail

# Configuration defaults
AWS_REGION="${AWS_REGION:-ap-south-1}"
FUNCTION_NAME="${FUNCTION_NAME:-banana-graph-brain}"
ECR_REPO_NAME="${ECR_REPO_NAME:-banana-graph-brain}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "=========================================================="
echo "🍌 Deploying Banana to AWS Lambda"
echo "Region: $AWS_REGION | Function: $FUNCTION_NAME"
echo "=========================================================="

# 1. Verify AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is not installed or not in PATH."
    echo "Install it via: https://aws.amazon.com/cli/"
    exit 1
fi

# 2. Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

echo "✓ AWS Account ID: $ACCOUNT_ID"
echo "✓ Target ECR URI: $ECR_URI:$IMAGE_TAG"

# 3. Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names "$ECR_REPO_NAME" --region "$AWS_REGION" > /dev/null 2>&1 || {
    echo "Creating ECR repository $ECR_REPO_NAME..."
    aws ecr create-repository --repository-name "$ECR_REPO_NAME" --region "$AWS_REGION"
}

# 4. Authenticate Docker with ECR
echo "Authenticating Docker with Amazon ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# 5. Build Lambda Container Image
echo "Building Docker container image for Lambda..."
docker build -t "$ECR_REPO_NAME:$IMAGE_TAG" -f Dockerfile.lambda .

# 6. Tag and Push to ECR
echo "Tagging and pushing container image to ECR..."
docker tag "$ECR_REPO_NAME:$IMAGE_TAG" "$ECR_URI:$IMAGE_TAG"
docker push "$ECR_URI:$IMAGE_TAG"

# 7. Create or Update Lambda Function
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$AWS_REGION" > /dev/null 2>&1; then
    echo "Updating existing Lambda function code..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --image-uri "$ECR_URI:$IMAGE_TAG" \
        --region "$AWS_REGION"
else
    echo "Creating new Lambda function with Function URL..."
    # Ensure IAM role exists or prompt
    ROLE_ARN=$(aws iam get-role --role-name lambda-basic-execution --query Role.Arn --output text 2>/dev/null || echo "")
    if [ -z "$ROLE_ARN" ]; then
        echo "⚠️ Note: Ensure your execution role exists with basic Lambda permissions."
        echo "Example: aws lambda create-function --function-name $FUNCTION_NAME --package-type Image --code ImageUri=$ECR_URI:$IMAGE_TAG --role <ROLE_ARN>"
        exit 0
    fi
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --package-type Image \
        --code ImageUri="$ECR_URI:$IMAGE_TAG" \
        --role "$ROLE_ARN" \
        --timeout 30 \
        --memory-size 512 \
        --region "$AWS_REGION"

    # Create Function URL for direct HTTPS access
    aws lambda create-function-url-config \
        --function-name "$FUNCTION_NAME" \
        --auth-type NONE \
        --region "$AWS_REGION"
fi

echo "=========================================================="
echo "🎉 Banana Serverless Deployment Complete!"
echo "=========================================================="
