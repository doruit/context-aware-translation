# Infrastructure as Code - Azure Translation Service

This directory contains Bicep templates for deploying the Azure Translation Service infrastructure.

## 📦 Resources Deployed

The infrastructure includes:

- **Azure Translator** (Cognitive Services) - Text translation with custom category support
- **Azure OpenAI** (Optional) - GPT-4 post-editor for fluency improvements
- **App Service Plan** - Linux plan for hosting Python 3.11 application
- **App Service** - Web application hosting
- **Storage Account** - Blob storage for glossary files
- **Application Insights** - Application monitoring and telemetry
- **Log Analytics** - Centralized logging

## 🚀 Deployment Methods

### Method 1: GitHub Actions (Recommended)

1. **Configure OIDC for GitHub Actions:**
   ```bash
   # Set variables
   GITHUB_ORG="doruit"
   GITHUB_REPO="context-aware-translation"
   SUBSCRIPTION_ID="your-subscription-id"
   
   # Create Azure AD App Registration
   az ad app create --display-name "GitHub-${GITHUB_REPO}"
   
   # Get App ID
   APP_ID=$(az ad app list --display-name "GitHub-${GITHUB_REPO}" --query "[0].appId" -o tsv)
   
   # Create Service Principal
   az ad sp create --id $APP_ID
   
   # Get Object ID
   OBJECT_ID=$(az ad sp show --id $APP_ID --query id -o tsv)
   
   # Assign Contributor role
   az role assignment create \
     --role Contributor \
     --subscription $SUBSCRIPTION_ID \
     --assignee-object-id $OBJECT_ID \
     --assignee-principal-type ServicePrincipal
   
   # Configure federated credentials
   az ad app federated-credential create \
     --id $APP_ID \
     --parameters '{
       "name": "GitHub-Actions",
       "issuer": "https://token.actions.githubusercontent.com",
       "subject": "repo:'"$GITHUB_ORG/$GITHUB_REPO"':environment:prod",
       "audiences": ["api://AzureADTokenExchange"]
     }'
   ```

2. **Add GitHub Secrets:**
   - `AZURE_CLIENT_ID`: Application (client) ID
   - `AZURE_TENANT_ID`: Directory (tenant) ID
   - `AZURE_SUBSCRIPTION_ID`: Subscription ID

3. **Run Workflow:**
   - Go to Actions → Deploy Infrastructure
   - Select environment and location
   - Click "Run workflow"

### Method 2: Azure CLI

```bash
# Make deploy script executable
chmod +x infra/deploy.sh

# Deploy to dev environment
./infra/deploy.sh dev rg-translation-dev westeurope

# Deploy to production
./infra/deploy.sh prod rg-translation-prod westeurope
```

### Method 3: Manual Deployment

```bash
# Set variables
ENVIRONMENT="dev"
RESOURCE_GROUP="rg-translation-$ENVIRONMENT"
LOCATION="westeurope"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Deploy Bicep template
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.$ENVIRONMENT.json \
  --name "translation-$(date +%Y%m%d-%H%M%S)"

# Get outputs
az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name <deployment-name> \
  --query "properties.outputs"
```

## 📋 Parameters

### `main.bicep` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `environment` | string | `dev` | Environment name (dev, staging, prod) |
| `location` | string | Resource Group location | Azure region for resources |
| `namePrefix` | string | `translate` | Prefix for all resource names |
| `enablePostEditor` | bool | `false` | Enable Azure OpenAI post-editor |
| `appServiceSku` | string | `B1` | App Service SKU (B1, B2, S1, P1v2, etc.) |
| `tags` | object | See template | Resource tags |

### Environment-Specific Parameters

**Development (`main.parameters.dev.json`)**
- Basic SKU (B1)
- Post-editor disabled
- Cost-optimized

**Production (`main.parameters.prod.json`)**
- Premium SKU (P1v2)
- Post-editor enabled
- High availability

## 🔧 Post-Deployment Configuration

### 1. Configure Custom Translator (Optional)

```bash
# Visit Custom Translator Portal
open https://portal.customtranslator.azure.ai/

# Create workspace and project
# Upload parallel training data
# Train model
# Get category ID
CATEGORY_ID="your-category-id"

# Update App Service configuration
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_SERVICE_NAME \
  --settings AZURE_TRANSLATOR_CATEGORY=$CATEGORY_ID
```

### 2. Deploy Azure OpenAI Model (If Enabled)

```bash
# Get OpenAI resource name
OPENAI_NAME=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name <deployment-name> \
  --query "properties.outputs.openaiName.value" -o tsv)

# Deploy GPT-4 model
az cognitiveservices account deployment create \
  --resource-group $RESOURCE_GROUP \
  --name $OPENAI_NAME \
  --deployment-name gpt-4 \
  --model-name gpt-4 \
  --model-version "0613" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard
```

### 3. Upload Glossary File

```bash
# Get storage account name
STORAGE_NAME=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name <deployment-name> \
  --query "properties.outputs.storageAccountName.value" -o tsv)

# Upload glossary
az storage blob upload \
  --account-name $STORAGE_NAME \
  --container-name glossaries \
  --name glossary.tsv \
  --file data/glossary.tsv \
  --auth-mode login
```

## 💰 Cost Estimation

### Development Environment

| Service | SKU | Estimated Monthly Cost |
|---------|-----|----------------------|
| Azure Translator | S1 | $10 + usage |
| App Service Plan | B1 | $13 |
| Storage Account | Standard LRS | $1 |
| Application Insights | Pay-as-you-go | $5 |
| **Total** | | **~$30/month** |

### Production Environment

| Service | SKU | Estimated Monthly Cost |
|---------|-----|----------------------|
| Azure Translator | S1 | $10 + usage |
| Azure OpenAI | S0 | $0 + usage |
| App Service Plan | P1v2 | $80 |
| Storage Account | Standard LRS | $1 |
| Application Insights | Pay-as-you-go | $20 |
| **Total** | | **~$115/month** |

*Prices are estimates and vary by region. Usage costs depend on translation volume.*

## 🔒 Security Considerations

- All resources use HTTPS only
- Storage accounts disable public blob access
- App Service uses managed identity where possible
- Secrets stored in Azure Key Vault (recommended for production)
- Network security groups can be added for additional security
- Consider using Azure Front Door or Application Gateway for production

## 🧹 Cleanup

```bash
# Delete entire resource group
az group delete --name $RESOURCE_GROUP --yes --no-wait

# Or delete specific deployment
az deployment group delete \
  --resource-group $RESOURCE_GROUP \
  --name <deployment-name>
```

## 📚 Additional Resources

- [Azure Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Azure Translator Documentation](https://learn.microsoft.com/azure/cognitive-services/translator/)
- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [App Service Documentation](https://learn.microsoft.com/azure/app-service/)
