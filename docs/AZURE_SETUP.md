# Azure Setup Guide

Complete guide for configuring Azure resources required for the translation service.

## Prerequisites

- Active Azure subscription
- Azure CLI installed (optional, for command-line setup)
- Access to Azure Portal

## Required Services

1. **Azure Translator Text** (Required)
2. **Azure Custom Translator** (Optional - for custom-trained models)
3. **Azure OpenAI** (Optional - for post-editing)

---

## 1. Azure Translator Text v3 Setup

Azure Translator provides the core translation capability.

### Option A: Azure Portal

1. **Navigate to Azure Portal**
   - Go to [https://portal.azure.com](https://portal.azure.com)
   - Sign in with your Azure account

2. **Create Translator Resource**
   - Click "Create a resource"
   - Search for "Translator"
   - Click "Create"

3. **Configure Resource**
   - **Subscription:** Select your subscription
   - **Resource Group:** Create new or select existing
   - **Region:** Choose closest to your users (e.g., `westeurope`)
   - **Name:** Choose unique name (e.g., `my-translator-service`)
   - **Pricing Tier:**
     - `F0` (Free): 2M characters/month
     - `S1` (Standard): Pay-as-you-go, 40 req/sec

4. **Review and Create**
   - Click "Review + create"
   - Click "Create"
   - Wait for deployment to complete

5. **Get Credentials**
   - Go to resource → "Keys and Endpoint"
   - Copy:
     - **Key 1** (or Key 2)
     - **Endpoint** (e.g., `https://api.cognitive.microsofttranslator.com`)
     - **Location/Region** (e.g., `westeurope`)

### Option B: Azure CLI

```bash
# Login to Azure
az login

# Create resource group
az group create \
  --name translator-rg \
  --location westeurope

# Create Translator resource
az cognitiveservices account create \
  --name my-translator-service \
  --resource-group translator-rg \
  --kind TextTranslation \
  --sku F0 \
  --location westeurope

# Get keys
az cognitiveservices account keys list \
  --name my-translator-service \
  --resource-group translator-rg
```

### Configuration

Add to your `.env` file:

```ini
AZURE_TRANSLATOR_KEY=your_key_from_step_5
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
AZURE_TRANSLATOR_REGION=westeurope
```

### Test Connection

```bash
# Test translation endpoint
curl -X POST "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=nl" \
  -H "Ocp-Apim-Subscription-Key: YOUR_KEY" \
  -H "Ocp-Apim-Subscription-Region: westeurope" \
  -H "Content-Type: application/json" \
  -d '[{"Text":"Hello, world!"}]'
```

Expected response:
```json
[
  {
    "translations": [
      {
        "text": "Hallo, wereld!",
        "to": "nl"
      }
    ]
  }
]
```

---

## 2. Azure Custom Translator Setup (Optional)

Custom Translator allows you to train domain-specific translation models.

### When to Use Custom Translator

✅ **Use Custom Translator if:**
- You have parallel training data (source + target language pairs)
- You need domain-specific context (e.g., medical, legal, technical)
- You want improved translation quality for specific terminology
- You have 10,000+ sentence pairs for training

❌ **Skip Custom Translator if:**
- You only need glossary enforcement (our service handles this)
- You don't have training data
- General translation quality is sufficient

### Setup Steps

1. **Navigate to Custom Translator Portal**
   - Go to [https://portal.customtranslator.azure.ai/](https://portal.customtranslator.azure.ai/)
   - Sign in with Azure account

2. **Create Workspace**
   - Click "Create workspace"
   - Name: e.g., "IT Support Translation"
   - Select your Translator resource
   - Click "Create"

3. **Create Project**
   - Click "New project"
   - **Name:** e.g., "English to Dutch IT"
   - **Source language:** English
   - **Target language:** Dutch
   - **Category:** Choose domain (e.g., "Technology")
   - Click "Create"

4. **Upload Training Data**
   - Click "Documents" → "Upload documents"
   - Upload parallel files:
     - `training.en.txt` (English sentences)
     - `training.nl.txt` (Dutch translations)
   - Files must have same number of lines
   - Minimum 10,000 sentence pairs recommended

5. **Train Model**
   - Click "Models" → "Train model"
   - Select training documents
   - Optionally add tuning/testing documents
   - Click "Train"
   - Wait for training to complete (can take hours)

6. **Get Category ID**
   - Once trained, go to "Models"
   - Click on your model
   - Copy **Category ID** (long alphanumeric string)

### Configuration

Add to your `.env` file:

```ini
AZURE_TRANSLATOR_CATEGORY=your_category_id_from_step_6
```

### Example Training Data Format

**training.en.txt:**
```
The service desk received a critical incident.
The customer reports the cash register is not working.
The store manager needs immediate help.
```

**training.nl.txt:**
```
De servicedesk ontving een incident.
De klant meldt dat de kassa niet werkt.
De filiaalbeheerder heeft onmiddellijke hulp nodig.
```

---

## 3. Azure OpenAI Setup (Optional)

Azure OpenAI provides GPT-4 for post-editing to improve translation fluency.

### When to Use Azure OpenAI Post-Editor

✅ **Use Post-Editor if:**
- Translation fluency is critical
- You need more natural-sounding output
- You can accept ~1-2s additional latency
- You have Azure OpenAI access

❌ **Skip Post-Editor if:**
- Speed is critical (< 1s latency requirement)
- Raw translation quality is sufficient
- You don't have Azure OpenAI access
- Cost optimization is priority

### Setup Steps

1. **Request Azure OpenAI Access**
   - Azure OpenAI requires application approval
   - Apply at: [https://aka.ms/oai/access](https://aka.ms/oai/access)
   - Wait for approval (can take days)

2. **Create Azure OpenAI Resource**
   - Azure Portal → "Create a resource"
   - Search for "Azure OpenAI"
   - Click "Create"
   - **Resource group:** Select or create
   - **Region:** Choose available region (e.g., `eastus`)
   - **Name:** e.g., `my-openai-service`
   - **Pricing tier:** Standard
   - Click "Review + create"

3. **Deploy GPT-4 Model**
   - Go to Azure OpenAI Studio: [https://oai.azure.com](https://oai.azure.com)
   - Navigate to "Deployments"
   - Click "Create new deployment"
   - **Model:** Select `gpt-4` or `gpt-4-turbo`
   - **Deployment name:** e.g., `gpt-4`
   - **Capacity:** Start with 10K tokens/min
   - Click "Create"

4. **Get Credentials**
   - Azure Portal → Your OpenAI resource
   - Go to "Keys and Endpoint"
   - Copy:
     - **Endpoint** (e.g., `https://my-openai-service.openai.azure.com/`)
     - **Key 1**
   - Note your **Deployment name** from step 3

### Configuration

Add to your `.env` file:

```ini
ENABLE_POST_EDITOR=true
AZURE_OPENAI_ENDPOINT=https://my-openai-service.openai.azure.com/
AZURE_OPENAI_KEY=your_key_from_step_4
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### Test Connection

```python
# test_openai.py
from openai import AzureOpenAI
import os

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

response = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    messages=[
        {"role": "user", "content": "Say hello!"}
    ]
)

print(response.choices[0].message.content)
```

---

## Cost Estimation

### Azure Translator

| Tier | Price | Included |
|------|-------|----------|
| F0 (Free) | $0 | 2M characters/month |
| S1 (Standard) | $10 per 1M characters | Pay-as-you-go |

**Example:** 100,000 translations × 100 chars = 10M chars = **$100/month**

### Custom Translator

- **Training:** Free (uses your Translator resource)
- **Translation:** Same as standard Translator pricing
- **Storage:** Minimal (training data)

### Azure OpenAI

| Model | Price (per 1K tokens) |
|-------|----------------------|
| GPT-4 | $0.03 (input) + $0.06 (output) |
| GPT-4 Turbo | $0.01 (input) + $0.03 (output) |

**Example:** 10,000 post-edits × 200 tokens = 2M tokens = **$60-120/month**

---

## Security Best Practices

### 1. Use Managed Identity (Production)

Instead of keys, use Azure Managed Identity:

```python
from azure.identity import DefaultAzureCredential
from azure.ai.translation.text import TextTranslationClient

credential = DefaultAzureCredential()
client = TextTranslationClient(
    endpoint="https://api.cognitive.microsofttranslator.com",
    credential=credential
)
```

### 2. Rotate Keys Regularly

- Azure Portal → Resource → "Keys and Endpoint"
- "Regenerate key 1" (while using key 2)
- Update application to use new key
- Regenerate key 2

### 3. Use Azure Key Vault

Store secrets in Key Vault instead of `.env`:

```bash
# Create Key Vault
az keyvault create \
  --name my-translator-vault \
  --resource-group translator-rg \
  --location westeurope

# Add secret
az keyvault secret set \
  --vault-name my-translator-vault \
  --name translator-key \
  --value "your_key_here"

# Grant application access
az keyvault set-policy \
  --name my-translator-vault \
  --object-id YOUR_APP_OBJECT_ID \
  --secret-permissions get list
```

### 4. Network Security

- Enable Azure Private Link for Translator resource
- Restrict IP access in Azure Portal
- Use Virtual Network Service Endpoints

---

## Monitoring and Diagnostics

### Enable Diagnostic Logging

1. Azure Portal → Your Translator resource
2. "Diagnostic settings" → "Add diagnostic setting"
3. Select logs to capture:
   - Audit logs
   - Request/response logs
   - Error logs
4. Send to:
   - Log Analytics workspace
   - Storage account
   - Event Hub

### Monitor Usage

```bash
# Get usage metrics
az monitor metrics list \
  --resource /subscriptions/YOUR_SUB/resourceGroups/translator-rg/providers/Microsoft.CognitiveServices/accounts/my-translator-service \
  --metric "CharactersTranslated" \
  --start-time 2024-02-01T00:00:00Z \
  --end-time 2024-02-04T23:59:59Z
```

### Set Up Alerts

1. Azure Portal → Resource → "Alerts"
2. "New alert rule"
3. Configure:
   - **Condition:** Characters translated > 1.5M
   - **Action:** Email notification
   - **Alert name:** "Translation quota warning"

---

## Troubleshooting

### Authentication Errors (401)

**Problem:** `Authentication failed`

**Solutions:**
- Verify key is correct (no extra spaces)
- Check key is not expired
- Ensure region matches (e.g., `westeurope`)
- Regenerate key if needed

### Rate Limiting (429)

**Problem:** `Too many requests`

**Solutions:**
- Implement exponential backoff
- Upgrade from F0 to S1 tier
- Distribute load across multiple resources

### Custom Category Not Found

**Problem:** `Category not found`

**Solutions:**
- Verify category ID is correct
- Ensure model training is complete
- Check model is published (not draft)

### OpenAI Deployment Not Found

**Problem:** `Deployment not found`

**Solutions:**
- Verify deployment name matches `.env`
- Ensure deployment is complete
- Check region supports your model

---

## Next Steps

- **[Quick Start](QUICKSTART.md)** - Configure and run the application
- **[API Guide](API_GUIDE.md)** - Integrate the API
- **[Testing Guide](TESTING_GUIDE.md)** - Validate your setup
- **[Main README](../README.md)** - Full documentation

---

## Support Resources

- **Azure Translator Docs:** [https://docs.microsoft.com/azure/cognitive-services/translator/](https://docs.microsoft.com/azure/cognitive-services/translator/)
- **Custom Translator Guide:** [https://docs.microsoft.com/azure/cognitive-services/translator/custom-translator/overview](https://docs.microsoft.com/azure/cognitive-services/translator/custom-translator/overview)
- **Azure OpenAI Docs:** [https://learn.microsoft.com/azure/ai-services/openai/](https://learn.microsoft.com/azure/ai-services/openai/)
- **Azure Support:** [https://azure.microsoft.com/support/](https://azure.microsoft.com/support/)
