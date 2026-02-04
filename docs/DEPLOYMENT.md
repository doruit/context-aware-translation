# Deployment Guide - Azure Translation Service

Complete guide for deploying the Translation Service to Azure with GitHub Actions CI/CD.

## 📋 Prerequisites

### Azure Requirements

1. **Azure Subscription** with permissions to create:
   - Cognitive Services (Translator, OpenAI)
   - App Services
   - Storage Accounts
   - Application Insights

2. **Azure CLI** installed and configured
   ```bash
   # Install Azure CLI
   brew install azure-cli  # macOS
   # or visit: https://learn.microsoft.com/cli/azure/install-azure-cli
   
   # Login
   az login
   
   # Set subscription
   az account set --subscription "your-subscription-id"
   ```

3. **Bicep CLI** (included with Azure CLI 2.20.0+)
   ```bash
   az bicep version
   ```

### GitHub Requirements

1. **GitHub Account** with repository access
2. **GitHub CLI** (optional, for automation)
   ```bash
   brew install gh  # macOS
   gh auth login
   ```

## 🚀 Deployment Steps

### Step 1: Repository Setup

1. **Create GitHub Repository:**
   ```bash
   # Recommended name: context-aware-translation
   gh repo create doruit/context-aware-translation --public
   ```

2. **Initialize Local Repository:**
   ```bash
   cd context-aware-translation
   git init
   git add .
   git commit -m "Initial commit: Azure Translation Service with Glossary"
   git branch -M main
   git remote add origin https://github.com/doruit/context-aware-translation.git
   git push -u origin main
   
   # Create develop branch
   git checkout -b develop
   git push -u origin develop
   ```

3. **Configure Branch Protection:**
   - Go to Settings → Branches
   - Add rule for `main` branch
   - Enable "Require pull request reviews"
   - Enable "Require status checks to pass"

### Step 2: Azure AD Application Setup (OIDC)

1. **Create Service Principal:**
   ```bash
   # Set variables
   export GITHUB_ORG="doruit"
   export GITHUB_REPO="context-aware-translation"
   export SUBSCRIPTION_ID=$(az account show --query id -o tsv)
   export TENANT_ID=$(az account show --query tenantId -o tsv)
   
   # Create AD App
   az ad app create --display-name "GitHub-${GITHUB_REPO}"
   
   # Get App ID
   export APP_ID=$(az ad app list --display-name "GitHub-${GITHUB_REPO}" --query "[0].appId" -o tsv)
   echo "AZURE_CLIENT_ID=$APP_ID"
   
   # Create Service Principal
   az ad sp create --id $APP_ID
   
   # Get Service Principal Object ID
   export SP_OBJECT_ID=$(az ad sp show --id $APP_ID --query id -o tsv)
   ```

2. **Assign Azure Permissions:**
   ```bash
   # Assign Contributor role at subscription level
   az role assignment create \
     --role Contributor \
     --subscription $SUBSCRIPTION_ID \
     --assignee-object-id $SP_OBJECT_ID \
     --assignee-principal-type ServicePrincipal
   ```

3. **Configure Federated Credentials:**
   ```bash
   # For each environment (dev, staging, prod)
   for ENV in dev staging prod; do
     az ad app federated-credential create \
       --id $APP_ID \
       --parameters "{
         \"name\": \"GitHub-${ENV}\",
         \"issuer\": \"https://token.actions.githubusercontent.com\",
         \"subject\": \"repo:${GITHUB_ORG}/${GITHUB_REPO}:environment:${ENV}\",
         \"audiences\": [\"api://AzureADTokenExchange\"]
       }"
   done
   
   # For main and develop branches
   for BRANCH in main develop; do
     az ad app federated-credential create \
       --id $APP_ID \
       --parameters "{
         \"name\": \"GitHub-${BRANCH}\",
         \"issuer\": \"https://token.actions.githubusercontent.com\",
         \"subject\": \"repo:${GITHUB_ORG}/${GITHUB_REPO}:ref:refs/heads/${BRANCH}\",
         \"audiences\": [\"api://AzureADTokenExchange\"]
       }"
   done
   ```

### Step 3: GitHub Secrets Configuration

1. **Add Repository Secrets:**
   ```bash
   # Using GitHub CLI
   gh secret set AZURE_CLIENT_ID --body "$APP_ID"
   gh secret set AZURE_TENANT_ID --body "$TENANT_ID"
   gh secret set AZURE_SUBSCRIPTION_ID --body "$SUBSCRIPTION_ID"
   ```

   Or manually in GitHub:
   - Go to Settings → Secrets and variables → Actions
   - Add new repository secrets:
     - `AZURE_CLIENT_ID`: Application (client) ID
     - `AZURE_TENANT_ID`: Directory (tenant) ID
     - `AZURE_SUBSCRIPTION_ID`: Subscription ID

2. **Configure Environments:**
   - Go to Settings → Environments
   - Create environments: `dev`, `staging`, `prod`
   - For `prod`: Enable "Required reviewers"

### Step 4: Deploy Infrastructure

1. **Deploy via GitHub Actions:**
   ```bash
   # Go to repository → Actions → Deploy Infrastructure
   # Click "Run workflow"
   # Select environment (dev/staging/prod)
   # Select location (westeurope, eastus, etc.)
   # Click "Run workflow"
   ```

2. **Or deploy locally:**
   ```bash
   # Make script executable
   chmod +x infra/deploy.sh
   
   # Deploy to dev
   ./infra/deploy.sh dev rg-translation-dev westeurope
   
   # Deploy to prod
   ./infra/deploy.sh prod rg-translation-prod westeurope
   ```

3. **Capture Outputs:**
   ```bash
   # Get deployment outputs
   az deployment group show \
     --resource-group rg-translation-dev \
     --name <deployment-name> \
     --query "properties.outputs" \
     -o json > deployment-outputs.json
   
   # Extract App Service name
   export APP_SERVICE_NAME=$(cat deployment-outputs.json | jq -r '.appServiceName.value')
   ```

### Step 5: Post-Deployment Configuration

#### Configure Custom Translator (Optional)

1. **Create Custom Translator Project:**
   - Visit: https://portal.customtranslator.azure.ai/
   - Sign in with Azure account
   - Create workspace
   - Create project (source → Dutch)
   - Upload parallel training data
   - Train model
   - Note the Category ID

2. **Update App Service:**
   ```bash
   az webapp config appsettings set \
     --resource-group rg-translation-dev \
     --name $APP_SERVICE_NAME \
     --settings AZURE_TRANSLATOR_CATEGORY="your-category-id"
   ```

#### Deploy Azure OpenAI Model (If Enabled)

```bash
# Get OpenAI resource name (if post-editor enabled)
export OPENAI_NAME=$(cat deployment-outputs.json | jq -r '.openaiName.value')

# Deploy GPT-4
az cognitiveservices account deployment create \
  --resource-group rg-translation-dev \
  --name $OPENAI_NAME \
  --deployment-name gpt-4 \
  --model-name gpt-4 \
  --model-version "0613" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard
```

#### Upload Glossary

```bash
# Get storage account
export STORAGE_NAME=$(cat deployment-outputs.json | jq -r '.storageAccountName.value')

# Upload glossary file
az storage blob upload \
  --account-name $STORAGE_NAME \
  --container-name glossaries \
  --name glossary.tsv \
  --file data/glossary.tsv \
  --auth-mode login
```

### Step 6: Configure App Service Deployment

1. **Add App Service Name to GitHub Secrets:**
   ```bash
   # For each environment
   gh secret set AZURE_APP_SERVICE_NAME --env dev --body "$APP_SERVICE_NAME"
   ```

2. **Enable Container Registry:**
   - GitHub automatically creates `ghcr.io` packages
   - Ensure Actions can push to GHCR (enabled by default)

### Step 7: Deploy Application

1. **Trigger CI/CD Pipeline:**
   ```bash
   # Push to develop branch (deploys to dev)
   git checkout develop
   git push origin develop
   
   # Or push to main (deploys to prod)
   git checkout main
   git merge develop
   git push origin main
   ```

2. **Monitor Deployment:**
   - Go to Actions tab
   - Watch CI/CD Pipeline workflow
   - Check each job (Test → Build → Deploy)

3. **Verify Deployment:**
   ```bash
   # Get App Service URL
   export APP_URL=$(cat deployment-outputs.json | jq -r '.appServiceUrl.value')
   
   # Check health endpoint
   curl $APP_URL/api/health
   
   # Open in browser
   open $APP_URL
   ```

## 🧪 Testing the Deployment

1. **Health Check:**
   ```bash
   curl https://$APP_SERVICE_NAME.azurewebsites.net/api/health
   ```

2. **Test Translation:**
   ```bash
   curl -X POST https://$APP_SERVICE_NAME.azurewebsites.net/api/translate \
     -H "Content-Type: application/json" \
     -d '{
       "text": "We have a critical incident in the service desk",
       "source_language": "en",
       "enable_post_editor": false
     }' | jq '.'
   ```

3. **Check Logs:**
   ```bash
   # Stream App Service logs
   az webapp log tail \
     --resource-group rg-translation-dev \
     --name $APP_SERVICE_NAME
   ```

## 📊 Monitoring and Maintenance

### Application Insights

1. **Access Application Insights:**
   - Azure Portal → Resource Group → Application Insights
   - View metrics, traces, and exceptions

2. **Query Logs:**
   ```kusto
   traces
   | where timestamp > ago(1h)
   | order by timestamp desc
   ```

### Update Glossary

```bash
# Upload new glossary version
az storage blob upload \
  --account-name $STORAGE_NAME \
  --container-name glossaries \
  --name glossary.tsv \
  --file data/glossary.tsv \
  --auth-mode login \
  --overwrite

# Restart app to reload
az webapp restart \
  --resource-group rg-translation-dev \
  --name $APP_SERVICE_NAME
```

### Scale Application

```bash
# Scale App Service Plan
az appservice plan update \
  --resource-group rg-translation-dev \
  --name $APP_SERVICE_PLAN_NAME \
  --sku P1v2

# Scale instances
az webapp scale \
  --resource-group rg-translation-dev \
  --name $APP_SERVICE_NAME \
  --instance-count 3
```

## 🔧 Troubleshooting

### Common Issues

**Issue: "Authentication failed"**
```bash
# Verify OIDC credentials
az ad app federated-credential list --id $APP_ID
```

**Issue: "Deployment failed - location not available"**
```bash
# Check available locations for services
az account list-locations -o table
az provider show --namespace Microsoft.CognitiveServices --query "resourceTypes[?resourceType=='accounts'].locations"
```

**Issue: "Container registry authentication failed"**
```bash
# Ensure GITHUB_TOKEN has package:write permission
# Check in Settings → Actions → General → Workflow permissions
```

**Issue: "App Service not starting"**
```bash
# Check logs
az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_SERVICE_NAME

# Check app settings
az webapp config appsettings list --resource-group $RESOURCE_GROUP --name $APP_SERVICE_NAME
```

## 🧹 Cleanup

```bash
# Delete entire resource group
az group delete --name rg-translation-dev --yes --no-wait

# Delete Azure AD App
az ad app delete --id $APP_ID

# Delete GitHub environments
gh api -X DELETE "repos/$GITHUB_ORG/$GITHUB_REPO/environments/dev"
```

## 📚 Next Steps

1. **Configure Custom Domain** (optional)
2. **Set up Azure Front Door** for global distribution
3. **Enable autoscaling** based on metrics
4. **Configure Azure Key Vault** for secrets management
5. **Set up monitoring alerts** in Application Insights
6. **Implement backup strategy** for glossary files

## 🔗 References

- [GitHub Actions - Azure Login](https://github.com/Azure/login)
- [Azure OIDC for GitHub Actions](https://learn.microsoft.com/azure/developer/github/connect-from-azure)
- [App Service Deployment](https://learn.microsoft.com/azure/app-service/deploy-github-actions)
- [Custom Translator](https://learn.microsoft.com/azure/cognitive-services/translator/custom-translator/overview)
