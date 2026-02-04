# Quick Start Guide

Get up and running with the Azure Translation Service with Glossary Enforcement in minutes.

## Prerequisites

- Python 3.11+
- Azure Translator Text resource
- (Optional) Azure Custom Translator category
- (Optional) Azure OpenAI resource

## Installation

### 1. Clone and Setup

```bash
# Navigate to project directory
cd action-translation-dict

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your Azure credentials
nano .env  # or use your preferred editor
```

**Required Configuration:**

```ini
# Azure Translator (REQUIRED)
AZURE_TRANSLATOR_KEY=your_key_from_azure_portal
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
AZURE_TRANSLATOR_REGION=westeurope

# Target Language (customize for your needs)
TARGET_LANGUAGE=nl  # Dutch, or change to: fr, de, es, it, etc.

# Custom Translator (OPTIONAL - leave empty to use default translation)
AZURE_TRANSLATOR_CATEGORY=your_custom_category_id

# Glossary
GLOSSARY_PATH=data/glossary.tsv

# Azure OpenAI Post-Editor (OPTIONAL)
ENABLE_POST_EDITOR=false
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_openai_key
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### 3. Create Glossary

Edit `data/glossary.tsv` with your domain-specific terminology:

```tsv
# source<TAB>target format
# IT Service Management (Contoso Corp example)
critical incident	incident
service desk	servicedesk
help desk	helpdesk
knowledge base	kennisbank
store manager	filiaalbeheerder
cash register	kassa
customer	klant
problem	probleem
ticket	ticket
priority	prioriteit
resolved	opgelost
pending	in behandeling

# Healthcare Example (uncomment to use)
# patient	patiënt
# prescription	voorschrift
# diagnosis	diagnose
# follow-up appointment	vervolgafspraak
# severe headache	ernstige hoofdpijn

# Legal Example (uncomment to use)
# contract	contract
# liability	aansprakelijkheid
# jurisdiction	rechtsgebied
# both parties	beide partijen
```

**Why These Terms Matter:**

Without glossary:
- "service desk" → "servicebalie" ❌ (literal translation, not company term)
- "critical incident" → "kritiek voorval" ❌ (inconsistent, should be "incident")
- "store manager" → "winkelbeheerder" ❌ (wrong, should be "filiaalbeheerder")

With glossary:
- "service desk" → "servicedesk" ✅ (company-specific compound)
- "critical incident" → "incident" ✅ (consistent terminology)
- "store manager" → "filiaalbeheerder" ✅ (correct domain term)

**Format Rules:**
- Tab-separated (source → target)
- One term per line
- Comments start with `#`
- Sorted longest-first automatically

### 4. Run Application

```bash
# Run with uvicorn
python -m src.app

# Or use uvicorn directly
uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
```

Access the web UI at: `http://localhost:8000`

## Quick Test

### Using the Web UI

1. Open `http://localhost:8000` in your browser
2. Select source language (e.g., English)
3. Enter text: "The service desk received a critical incident"
4. Click "Translate"
5. See the enforced translation with highlighted glossary terms

### Using the API

```bash
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
  "text": "The service desk received a critical incident",
  "source_language": "en",
  "enable_post_editor": false,
  "use_custom_category": false
}'
```

## Next Steps

- **[API Guide](API_GUIDE.md)** - Detailed API documentation and examples
- **[Azure Setup](AZURE_SETUP.md)** - Configure Custom Translator and Azure OpenAI
- **[Testing Guide](TESTING_GUIDE.md)** - Run tests and validate your setup
- **[Main README](../README.md)** - Full documentation and architecture details

## Troubleshooting

**"Glossary file not found"**
- Create `data/glossary.tsv` with at least one term
- Check `GLOSSARY_PATH` in `.env`

**"Translation failed: 401"**
- Verify `AZURE_TRANSLATOR_KEY` is correct
- Check key is not expired in Azure Portal

**"Post-editor unavailable"**
- Set `ENABLE_POST_EDITOR=true`
- Verify `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_KEY`
- Check deployment name matches

**"Terms not being enforced"**
- Verify TSV format (tab-separated, not spaces)
- Check term spelling matches translation output
- Try simpler terms first to verify system works
