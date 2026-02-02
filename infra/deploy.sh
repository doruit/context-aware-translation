#!/bin/bash
set -e

# Deploy Azure infrastructure using Bicep
# Usage: ./deploy.sh <environment> <resource-group> <location>

ENVIRONMENT=${1:-dev}
RESOURCE_GROUP=${2:-rg-translation-$ENVIRONMENT}
LOCATION=${3:-westeurope}

echo "======================================"
echo "Azure Translation Service Deployment"
echo "======================================"
echo "Environment: $ENVIRONMENT"
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "======================================"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI is not installed"
    exit 1
fi

# Check if logged in
echo "Checking Azure login status..."
az account show > /dev/null 2>&1 || {
    echo "Not logged in. Running 'az login'..."
    az login
}

# Create resource group if it doesn't exist
echo "Creating resource group if needed..."
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --tags Environment="$ENVIRONMENT" Application="translation-service"

# Validate Bicep template
echo "Validating Bicep template..."
az deployment group validate \
    --resource-group "$RESOURCE_GROUP" \
    --template-file infra/main.bicep \
    --parameters "infra/main.parameters.$ENVIRONMENT.json"

# Deploy infrastructure
echo "Deploying infrastructure..."
az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file infra/main.bicep \
    --parameters "infra/main.parameters.$ENVIRONMENT.json" \
    --name "translation-deployment-$(date +%Y%m%d-%H%M%S)"

# Get outputs
echo ""
echo "======================================"
echo "Deployment Complete!"
echo "======================================"
echo "Retrieving deployment outputs..."

DEPLOYMENT_NAME=$(az deployment group list \
    --resource-group "$RESOURCE_GROUP" \
    --query "[0].name" -o tsv)

az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --query "properties.outputs" \
    -o json

echo ""
echo "Next steps:"
echo "1. Configure Custom Translator category (if needed)"
echo "2. Deploy Azure OpenAI model (if enabled)"
echo "3. Upload glossary file to storage"
echo "4. Deploy application code"
echo ""
