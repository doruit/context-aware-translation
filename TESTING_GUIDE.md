# Testing Guide for ACTION Translation Service

## Overview
This guide provides step-by-step instructions for testing the translation service with the ACTION retail glossary.

## Prerequisites

✅ **Completed:**
- Azure infrastructure deployed to subscription `<your-subscription-id>`
- Python virtual environment created with Python 3.11
- All dependencies installed (latest versions as of 2025-01)
- ACTION retail glossary created (204 terms)
- Bicep templates updated with latest Azure API versions

## Recent Updates

### 1. Azure API Versions Updated
All Bicep templates now use the latest stable API versions:
- `Microsoft.CognitiveServices/accounts`: `2025-10-01-preview`
- `Microsoft.Web/sites`: `2025-03-01`
- `Microsoft.Web/serverfarms`: `2025-03-01`
- `Microsoft.Storage/storageAccounts`: `2025-06-01`
- `Microsoft.OperationalInsights/workspaces`: `2025-07-01`
- `Microsoft.Insights/components`: `2020-02-02-preview`

### 2. Python Dependencies Updated
All packages updated to latest versions:
- FastAPI: `0.115.6` (was 0.109.0)
- Uvicorn: `0.34.0` (was 0.27.0)
- Pydantic: `2.10.6` (was 2.5.3)
- OpenAI SDK: `2.16.0` (was azure-ai-openai 1.0.0b1)
- Azure Identity: `1.20.0` (was 1.15.0)
- Pytest: `8.3.5` (was 7.4.4)
- Black: `25.1.0` (was 24.1.1)
- Ruff: `0.9.3` (was 0.1.14)

### 3. Virtual Environment Ready
```bash
# Venv location
/Users/doruit/action-translation-dict/venv

# Python version
Python 3.11

# Activation
source venv/bin/activate
```

## Deployed Azure Resources

**Resource Group:** `rg-translation-dev` (West Europe)

| Resource Type | Name | Endpoint/URL |
|--------------|------|--------------|
| Translator Service | `translate-translator-dev-<unique-suffix>` | Custom endpoint |
| App Service | `translate-app-dev-<unique-suffix>` | https://translate-app-dev-<unique-suffix>.azurewebsites.net |
| Storage Account | `translate<unique-suffix>` | Blob storage for glossaries |
| Application Insights | `translate-insights-dev-<unique-suffix>` | Monitoring & logging |
| Log Analytics | `translate-logs-dev-<unique-suffix>` | Log aggregation |
| App Service Plan | `translate-plan-dev-<unique-suffix>` | B1 Linux plan |

## Testing Steps

### Step 1: Upload Glossary to Azure Storage

```bash
# Activate venv
source venv/bin/activate

# Upload glossary to blob storage
az storage blob upload \
  --account-name translate<unique-suffix> \
  --container-name glossaries \
  --name glossary.tsv \
  --file data/glossary.tsv \
  --auth-mode login
```

### Step 2: Configure Environment Variables

```bash
# Get Translator API key
TRANSLATOR_KEY=$(az cognitiveservices account keys list \
  --name translate-translator-dev-<unique-suffix> \
  --resource-group rg-translation-dev \
  --query "key1" -o tsv)

# Get Translator endpoint
TRANSLATOR_ENDPOINT=$(az cognitiveservices account show \
  --name translate-translator-dev-<unique-suffix> \
  --resource-group rg-translation-dev \
  --query "properties.endpoint" -o tsv)

# Create .env file for local testing
cat > .env << EOF
# Azure Translator
AZURE_TRANSLATOR_KEY=${TRANSLATOR_KEY}
AZURE_TRANSLATOR_ENDPOINT=${TRANSLATOR_ENDPOINT}
AZURE_TRANSLATOR_REGION=westeurope
AZURE_TRANSLATOR_CATEGORY=

# Translation Settings
TARGET_LANGUAGE=nl
GLOSSARY_PATH=data/glossary.tsv

# Optional: Azure OpenAI (if enabled)
ENABLE_POST_EDITOR=false
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_KEY=
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=true
EOF

echo "✅ Environment variables configured"
```

### Step 3: Test Locally

```bash
# Ensure venv is activated
source venv/bin/activate

# Run the application
python run.py

# Expected output:
# INFO:     Started server process [xxxxx]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Test API Endpoints

**Open a new terminal and test:**

```bash
# Health check
curl http://localhost:8000/health

# Test translation with ACTION terminology
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Please contact the service desk for help with your gift card.",
    "target_language": "nl"
  }'

# Expected: Dutch translation with "servicedesk" and "cadeaukaart" preserved
```

### Step 5: Test Web UI

```bash
# Open browser
open http://localhost:8000

# Test with ACTION retail scenarios:
1. Service desk ticket: "The customer cannot access their account at the service desk"
2. Store operations: "Please check the stock levels in the cash register system"
3. Training: "All staff must complete action academy management skills training"
4. Customer service: "The customer wants to return items without a receipt"
```

### Step 6: Verify Glossary Enforcement

Test these specific ACTION terms from the glossary:

| English | Expected Dutch | Test Sentence |
|---------|---------------|---------------|
| service desk | servicedesk | "Contact the service desk" |
| gift card | cadeaukaart | "Purchase a gift card" |
| cash register | kassa | "Use the cash register" |
| action academy | action academy | "Complete action academy training" |
| checkout | kassa | "Go to the checkout" |
| receipt | kassabon | "Show your receipt" |
| store manager | filiaalmanager | "Ask the store manager" |

### Step 7: Deploy to Azure App Service

```bash
# Configure App Service environment variables
az webapp config appsettings set \
  --name translate-app-dev-<unique-suffix> \
  --resource-group rg-translation-dev \
  --settings \
    AZURE_TRANSLATOR_KEY="${TRANSLATOR_KEY}" \
    AZURE_TRANSLATOR_ENDPOINT="${TRANSLATOR_ENDPOINT}" \
    AZURE_TRANSLATOR_REGION=westeurope \
    TARGET_LANGUAGE=nl \
    GLOSSARY_PATH=data/glossary.tsv \
    ENABLE_POST_EDITOR=false \
    HOST=0.0.0.0 \
    PORT=8000 \
    DEBUG=false

# Push to develop branch to trigger CI/CD
git add .
git commit -m "Updated to latest Azure API versions and Python packages"
git push origin develop

# Monitor deployment
az webapp log tail \
  --name translate-app-dev-<unique-suffix> \
  --resource-group rg-translation-dev
```

### Step 8: Test Production Deployment

```bash
# Test health endpoint
curl https://translate-app-dev-<unique-suffix>.azurewebsites.net/health

# Test translation API
curl -X POST https://translate-app-dev-<unique-suffix>.azurewebsites.net/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Please check the stock levels at the service desk",
    "target_language": "nl"
  }'

# Access web UI
open https://translate-app-dev-<unique-suffix>.azurewebsites.net
```

## Test Scenarios for ACTION Retail

### Scenario 1: Service Desk Ticket
**Input:**
```
A customer reported that their gift card is not working at the checkout. 
The service desk should help them verify the balance.
```

**Expected:**
- Dutch translation
- "gift card" → "cadeaukaart"
- "checkout" → "kassa"
- "service desk" → "servicedesk"

### Scenario 2: Store Operations
**Input:**
```
All store managers must complete the action academy management skills training 
before the end of Q1. Please check the cash register system for updates.
```

**Expected:**
- "store managers" → "filiaalmanagers" or "filiaalbeheerders"
- "action academy" → "action academy" (preserved)
- "management skills" → "management vaardigheden" (preserved)
- "cash register system" → "kassasysteem"

### Scenario 3: Customer Service
**Input:**
```
The customer wants to return items without a receipt. 
Please contact the store manager for approval.
```

**Expected:**
- "return items" → appropriate Dutch
- "receipt" → "kassabon"
- "store manager" → "filiaalmanager"

### Scenario 4: Security Alert
**Input:**
```
Security alarm activated at the store entrance. 
Check the alarm system and review camera footage.
```

**Expected:**
- "alarm" → "alarm" (preserved)
- "alarm system" → "alarmsysteem"
- "camera" → "camera" (preserved)

## Monitoring & Debugging

### View Application Logs
```bash
az webapp log tail \
  --name translate-app-dev-<unique-suffix> \
  --resource-group rg-translation-dev
```

### View Application Insights
```bash
# Get Application Insights instrumentation key
az monitor app-insights component show \
  --app translate-insights-dev-<unique-suffix> \
  --resource-group rg-translation-dev \
  --query "instrumentationKey" -o tsv

# Access in Azure Portal
open "https://portal.azure.com/#resource/subscriptions/<your-subscription-id>/resourceGroups/rg-translation-dev/providers/microsoft.insights/components/translate-insights-dev-<unique-suffix>"
```

### Check Storage Container
```bash
# List glossary files
az storage blob list \
  --account-name translate<unique-suffix> \
  --container-name glossaries \
  --auth-mode login \
  --output table
```

## Running Tests

```bash
# Activate venv
source venv/bin/activate

# Run unit tests
pytest tests/unit -v

# Run integration tests
pytest tests/integration -v

# Run with coverage
pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Troubleshooting

### Issue: Translation not using glossary
**Solution:** Verify glossary path and format
```bash
# Check glossary file
cat data/glossary.tsv | head -20

# Verify format (tab-separated, lowercase first column)
```

### Issue: Authentication errors
**Solution:** Verify API keys and endpoints
```bash
# Test Translator API directly
curl -X POST "${TRANSLATOR_ENDPOINT}/translate?api-version=3.0&to=nl" \
  -H "Ocp-Apim-Subscription-Key: ${TRANSLATOR_KEY}" \
  -H "Content-Type: application/json" \
  -d '[{"Text":"Hello world"}]'
```

### Issue: App Service not starting
**Solution:** Check deployment logs
```bash
# SSH into App Service
az webapp ssh \
  --name translate-app-dev-<unique-suffix> \
  --resource-group rg-translation-dev

# Check Python version
python --version

# Check installed packages
pip list
```

## Next Steps

1. ✅ Upload glossary to Azure Storage
2. ✅ Configure local environment
3. ✅ Test locally with ACTION scenarios
4. ✅ Verify glossary enforcement
5. ✅ Deploy to Azure App Service
6. ✅ Test production deployment
7. 📊 Monitor usage in Application Insights
8. 🔄 Set up CI/CD for automatic deployments
9. 📝 Document common translation patterns
10. 🎯 Optimize glossary based on real usage

## Glossary Statistics

- **Total terms:** 204 term pairs
- **Categories:** Service desk, store operations, customer service, training, payment, security, inventory, staff roles
- **Coverage:** English → Dutch with case variation support
- **Format:** TSV (tab-separated values)

## Performance Expectations

- **API latency:** < 500ms for typical requests
- **Throughput:** ~100 requests/minute on B1 tier
- **Glossary lookup:** O(n) scan (204 terms)
- **Uptime:** 99.9% SLA (App Service Standard+)

## Security Considerations

- ✅ HTTPS only (enforced)
- ✅ API key authentication (Azure Translator)
- ✅ Private blob storage (no public access)
- ✅ Managed identity support (planned)
- ✅ Application Insights for audit trail
