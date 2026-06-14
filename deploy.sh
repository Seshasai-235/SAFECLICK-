#!/bin/bash

# SafeClick Deployment Script

set -e

echo "🚀 SafeClick Deployment Script"
echo "================================"

# Check environment argument
ENV=${1:-dev}

if [ "$ENV" != "dev" ] && [ "$ENV" != "prod" ]; then
    echo "❌ Invalid environment. Use 'dev' or 'prod'"
    exit 1
fi

echo "📦 Environment: $ENV"
echo ""

# Install Node.js dependencies
echo "📥 Installing Node.js dependencies..."
cd src/api-handler && npm install && cd ../..
cd src/web-crawler && npm install && cd ../..

# Install Python dependencies
echo "📥 Installing Python dependencies..."
cd src/analyzer
pip install -r requirements.txt -t . --upgrade
cd ../..

cd src/results-handler
pip install -r requirements.txt -t . --upgrade
cd ../..

# Build SAM application
echo "🔨 Building SAM application..."
sam build

# Deploy
echo "🚀 Deploying to $ENV..."
if [ "$ENV" == "dev" ]; then
    sam deploy --config-env dev --no-confirm-changeset
else
    sam deploy --config-env prod
fi

# Get outputs
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name safeclick-$ENV \
    --query 'Stacks[0].Outputs' \
    --output table

echo ""
echo "🔗 API Endpoint:"
aws cloudformation describe-stacks \
    --stack-name safeclick-$ENV \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text

echo ""
echo "✨ Done!"
