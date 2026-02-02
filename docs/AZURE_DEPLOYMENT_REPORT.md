# Azure Translation Service - Deployment Report

**Deployment Date:** February 2, 2026  
**Status:** ✅ **SUCCESSFUL**

## Deployment Summary

### Resource Group
- **Name:** `rg-translation-dev`
- **Location:** West Europe (westeurope)
- **Subscription:** Microsoft GenAI (<your-subscription-id>)
- **Tenant:** <your-tenant-id>

---

## Deployed Resources

### 1. Azure Translator Service
- **Resource Name:** `translate-translator-dev-<unique-suffix>`
- **Type:** Microsoft.CognitiveServices/accounts
- **Kind:** TextTranslation
- **SKU:** S1
- **Endpoint:** `https://api.cognitive.microsofttranslator.com/`
- **Location:** West Europe
- **Status:** ✅ Deployed and running

**Next Steps:**
```bash
# Get API key for translator
az cognitiveservices account keys list \
  --name translate-translator-dev-<unique-suffix> \
  --resource-group rg-translation-dev
```

### 2. App Service (Web Application)
- **Resource Name:** `translate-app-dev-<unique-suffix>`
- **Type:** Microsoft.Web/sites
- **App Service Plan:** `translate-plan-dev-<unique-suffix>` (B1)
- **URL:** `https://translate-app-dev-<unique-suffix>.azurewebsites.net`
- **Runtime:** Python 3.11 (via deployment)
- **Location:** West Europe
- **Status:** ✅ Deployed

**Access:**
```bash
# Visit web UI
open https://translate-app-dev-<unique-suffix>.azurewebsites.net

# Check health
curl https://translate-app-dev-<unique-suffix>.azurewebsites.net/health
```

### 3. Storage Account (Glossary & Artifacts)
- **Resource Name:** `translate<unique-suffix>`
- **Type:** Microsoft.Storage/storageAccounts
- **Replication:** LRS (Locally Redundant)
- **Access Tier:** Hot
- **Location:** West Europe
- **Status:** ✅ Deployed
- **Container:** `glossaries` (created automatically)

**Upload Glossary:**
```bash
# Upload glossary.tsv to storage
az storage blob upload \
  --file data/glossary.tsv \
  --container-name glossaries \
  --name glossary.tsv \
  --account-name translate<unique-suffix>
```

### 4. Application Insights (Monitoring)
- **Resource Name:** `translate-insights-dev-<unique-suffix>`
- **Type:** Microsoft.Insights/components
- **Location:** West Europe
- **Instrumentation Key:** `<your-instrumentation-key>`
- **Status:** ✅ Deployed

**Access Metrics:**
```bash
# View in Azure Portal
https://portal.azure.com → Application Insights → translate-insights-dev-<unique-suffix>
```

### 5. Log Analytics Workspace
- **Resource Name:** `translate-logs-dev-<unique-suffix>`
- **Type:** Microsoft.OperationalInsights/workspaces
- **Location:** West Europe
- **Status:** ✅ Deployed

**View Logs:**
```bash
# Query logs via Azure Portal
https://portal.azure.com → Log Analytics workspaces → translate-logs-dev-<unique-suffix>
```

---

## Configuration Next Steps

### 1. Update .env File with Azure Resources

```bash
# Get Translator key
TRANSLATOR_KEY=$(az cognitiveservices account keys list \
  --name translate-translator-dev-<unique-suffix> \
  --resource-group rg-translation-dev \
  --query 'key1' -o tsv)

# Update .env
sed -i.bak "s|AZURE_TRANSLATOR_KEY=.*|AZURE_TRANSLATOR_KEY=$TRANSLATOR_KEY|" .env
sed -i.bak "s|AZURE_TRANSLATOR_REGION=.*|AZURE_TRANSLATOR_REGION=westeurope|" .env
```

### 2. Upload Glossary to Storage

```bash
# Create glossaries container (if not exists)
az storage container create \
  --name glossaries \
  --account-name translate<unique-suffix>

# Upload glossary file
az storage blob upload \
  --file data/glossary.tsv \
  --container-name glossaries \
  --name glossary.tsv \
  --account-name translate<unique-suffix> \
  --overwrite
```

### 3. Configure App Service Environment Variables

```bash
# Set App Service configuration
az webapp config appsettings set \
  --name translate-app-dev-<unique-suffix> \
  --resource-group rg-translation-dev \
  --settings \
    AZURE_TRANSLATOR_KEY="$TRANSLATOR_KEY" \
    AZURE_TRANSLATOR_REGION="westeurope" \
    TARGET_LANGUAGE="nl" \
    ENABLE_POST_EDITOR="false" \
    APPINSIGHTS_INSTRUMENTATION_KEY="<your-instrumentation-key>"
```

### 4. Deploy Application Code

Choose one:

**Option A: Via Deployment Script**
```bash
# Using deployment script
./infra/deploy.sh deploy-app dev
```

**Option B: Manual Deployment**
```bash
# Zip application
cd /Users/doruit/action-translation-dict
zip -r app.zip src/ requirements.txt run.py .env

# Deploy via Azure CLI
az webapp deployment source config-zip \
  --resource-group rg-translation-dev \
  --name translate-app-dev-<unique-suffix> \
  --src-path app.zip
```

**Option C: GitHub Actions (Recommended)**
```bash
# Push to GitHub and CI/CD handles deployment
git push origin main
```

---

## Testing the Deployment

### 1. Check Health Endpoint
```bash
curl https://translate-app-dev-<unique-suffix>.azurewebsites.net/health
# Expected response: {"status":"ok"}
```

### 2. Test Translation via API
```bash
curl -X POST https://translate-app-dev-<unique-suffix>.azurewebsites.net/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "source_language": "en",
    "text": "Hello, world!",
    "apply_glossary": true
  }' | jq .
```

### 3. Web UI Test
Open browser: `https://translate-app-dev-<unique-suffix>.azurewebsites.net`

---

## Resource Costs

**Estimated Monthly Costs (dev environment):**

| Resource | SKU | Monthly Cost |
|----------|-----|--------------|
| Azure Translator | S1 (50M chars) | ~$40 |
| App Service Plan | B1 | ~$13 |
| Storage Account | 5GB LRS | ~$1 |
| Application Insights | Free tier (1GB/day) | Free |
| Log Analytics | Free tier | Free |
| **Total** | | **~$54/month** |

**Note:** Costs scale with usage. S1 includes 50M characters/month; overage is ~$15 per million characters.

---

## Troubleshooting

### App Service Not Responding
```bash
# Check if app service is running
az webapp show \
  --name translate-app-dev-<unique-suffix> \
  --resource-group rg-translation-dev \
  --query "state" -o tsv

# View app service logs
az webapp log tail \
  --name translate-app-dev-<unique-suffix> \
  --resource-group rg-translation-dev
```

### Translator Service Not Accessible
```bash
# Verify service is running
az cognitiveservices account show \
  --name translate-translator-dev-<unique-suffix> \
  --resource-group rg-translation-dev \
  --query "{Status: properties.provisioningState, Kind: kind}"
```

### Storage Upload Issues
```bash
# Verify storage account
az storage account show \
  --name translate<unique-suffix> \
  --resource-group rg-translation-dev \
  --query "{Name: name, Status: provisioningState}"
```

---

## Scaling & Production

### For Production Environment
```bash
# Deploy to prod resource group
RESOURCE_GROUP="rg-translation-prod"
LOCATION="westeurope"

az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.prod.json \
  --parameters environment=prod \
  --parameters appServiceSku=S2
```

### High-Volume Scaling
For >100M characters/month:
1. Upgrade Translator to `S2` or `S3`
2. Upgrade App Service Plan to `S2` or `P1v2`
3. Enable Storage Account replication to `GRS` (Geo-Redundant)

---

## Monitoring & Alerts

### Enable Alert Rules
```bash
# CPU > 80%
az monitor metrics alert create \
  --name "HighCPU-translate-app" \
  --resource-group rg-translation-dev \
  --scopes "/subscriptions/<your-subscription-id>/resourceGroups/rg-translation-dev/providers/Microsoft.Web/sites/translate-app-dev-<unique-suffix>" \
  --condition "avg Percentage CPU > 80" \
  --action email admin@example.com
```

### View Application Insights
```bash
# Query performance metrics
az monitor app-insights metrics show \
  --resource-group rg-translation-dev \
  --component translate-insights-dev-<unique-suffix> \
  --metrics requests/rate
```

---

## Resource Tags

All resources tagged with:
- `Environment`: dev
- `Application`: translation-service
- `ManagedBy`: Bicep

---

## Cleanup (if needed)

```bash
# DELETE entire resource group (WARNING: Irreversible)
az group delete \
  --name rg-translation-dev \
  --yes
```

---

## Contact & Support

- **Documentation:** See [DEPLOYMENT.md](../DEPLOYMENT.md)
- **Infrastructure Code:** See [infra/README.md](../infra/README.md)
- **GitHub Workflows:** See [.github/workflows/](../.github/workflows/)
