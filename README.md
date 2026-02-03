# Azure Translation Service with Glossary Enforcement

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Azure](https://img.shields.io/badge/Azure-Translator-0078D4?logo=microsoft-azure)](https://azure.microsoft.com/services/cognitive-services/translator/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)](https://hub.docker.com/)

A production-ready service for translating text to any target language using **Azure Translator Text v3** with **Custom Translator** categories and deterministic **TSV glossary enforcement**. Preserve domain-specific terminology while improving fluency with optional **Azure OpenAI** post-editing.

<!-- <div align="center">
    <img src="https://github.com/doruit/azure-translation-glossary/blob/main/src/ui/media/screenshot1.png?raw=true" alt="UI Screenshot" width="100%" />
</div> -->

> **Live demonstration:** The service enforces glossary terms like "critical incident" → "incident" and "service desk" → "servicedesk", preserving them correctly during translation.

## 🎯 The Problem This Solves

### Real-World Challenge: Contoso Corp Case Study

**Contoso Corp**, a multinational retail and service organization, needed to translate customer support tickets in real-time through their ServiceNow platform. The core challenge:

> "We need **real-time translation** for customer support tickets, but also **guaranteed terminology consistency**. Our technical terms, product names, and internal jargon must ALWAYS translate the same way, regardless of context. However, Azure's Text Translation API doesn't natively support glossary injection like Document Translation does."

**The Tension:**
- **Real-time requirement:** Support tickets need fast translation (~1s latency) to keep customer support flowing
- **Terminology demand:** Consistent translation of company-specific terms (e.g., "critical incident" → "incident", "service desk" → "servicedesk")
- **API limitation:** Azure Text Translation API lacks built-in glossary support for real-time scenarios

**The Solution:** This service implements a **two-layer enforcement mechanism**:
1. **Azure Translator Text v3** for native NMT quality (~300-500ms latency)
2. **Deterministic Glossary Enforcer** to guarantee term consistency (100% deterministic, ~10-50ms overhead)

Result: **< 1 second latency with guaranteed terminology consistency**

---

## 🎯 Use Cases

- **IT Service Management**: Translate support tickets while preserving technical terms
- **Healthcare**: Maintain medical terminology accuracy across languages
- **Legal**: Ensure legal terms remain consistent in translations
- **Customer Support**: Translate user messages while keeping product names intact
- **Technical Documentation**: Preserve technical jargon during localization

## 🎯 Features

- **Real-time Translation Pipeline**
  1. Azure Translator Text v3 API (with custom category support)
  2. Deterministic glossary term enforcement (regex-based, case-preserving)
  3. Optional Azure OpenAI post-editing (GPT-4) for fluency

- **Glossary Enforcement**
  - TSV-based terminology management
  - Longest-match-first to handle overlapping terms
  - Case preservation (uppercase, titlecase, lowercase)
  - Word-boundary detection to avoid partial matches
  - Audit trail of all applied terms

- **Web UI**
  - Simple, responsive interface
  - Source language selection (de, fr, pl, es, it, en)
  - Real-time translation with visual diff
  - Shows raw, enforced, and final translations side-by-side
  - Highlights applied glossary terms

- **Production-Ready**
  - Comprehensive unit tests
  - Environment-based configuration
  - Health check endpoint
  - Low latency (< 2s typical)

## 🏗️ Architecture: Why This Works

### The Three-Layer Translation Pipeline

```
[Layer 1] Azure Translator Text v3
          └─→ Native neural translation, context-aware
             └─→ ~300-500ms latency
                └─→ Optional: Use custom-trained model (category parameter)

[Layer 2] Deterministic Glossary Enforcer
          └─→ 100% guaranteed term replacement
             └─→ Case-preserving (Service Desk → Servicedesk)
                └─→ Word-boundary detection (incident vs incidental)
                   └─→ Audit trail of all replacements
                      └─→ ~10-50ms overhead (negligible)

[Layer 3] Optional Azure OpenAI Post-Editor
          └─→ Improves fluency without changing terms
             └─→ System prompt: "DO NOT change glossary terms"
                └─→ Validation: confirms all terms still present
```

**Why Two Layers?**
- **Scenario A:** You have a custom-trained model → Use native Custom Translator support
- **Scenario B:** You don't have custom training → Deterministic regex enforcer guarantees consistency
- **Result:** Works in both cases, and provides audit trail for compliance

### Real Example: Contoso Corp Support Ticket

**Input (English):**
```
"We have a critical incident affecting the service desk. 
 Please escalate this problem to the knowledge base team."
```

**Step 1 - Raw Translation:**
```
"We hebben een critical incident dat de service desk raakt. 
 Escaleer dit problem naar het kennisbank team."
```

**Step 2 - Glossary Enforcement** (applying Contoso glossary):
```
"We hebben een CRITICAL INCIDENT (→ incident) dat de SERVICE DESK (→ servicedesk) raakt.
 Escaleer dit PROBLEM (→ probleem) naar het KNOWLEDGE BASE (→ kennisbank) team."

Result: "We hebben een incident dat de servicedesk raakt. 
         Escaleer dit probleem naar het kennisbank team."
```

**Step 3 - Optional Post-Edit** (improve fluency):
```
"We hebben een incident dat het servicedesk team raakt. 
 Escaleer dit probleem naar het kennisbank team."
```

**Guarantee:** No matter how many similar tickets, "critical incident" ALWAYS becomes "incident", "service desk" ALWAYS becomes "servicedesk".

---

## 📋 Requirements

- Python 3.11+
- Azure Translator Text resource
- (Optional) Azure Custom Translator category
- (Optional) Azure OpenAI resource

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone repository
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
domain-specific terminology:

```tsv
# source<TAB>target format
# Retail & Service Management Example (Contoso Corp)
incident	incident
problem	probleem
critical incident	incident
service desk	servicedesk
help desk	helpdesk
customer	klant
cash register	kassa
store manager	filiaalbeheerder
knowledge base	kennisbank
ticket	ticket
priority	prioriteit
resolved	opgelost
pending	in behandeling

# Healthcare Example
# diagnosis	diagnose
# patient	patiënt
# prescription	voorschrift

# Legal Example
# contract	contract
# liability	aansprakelijkheid
# jurisdiction	rechtsgebiedverzoek
```

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
affecting multiple users",
  "source_language": "en",
  "enable_post_editor": false,
  "use_custom_category": true
}
```

**Response:**
```json
{
  "raw_translation": "We hebben een critical incident dat meerdere gebruikers treft",
  "enforced_translation": "We hebben een kritiek incident dat meerdere gebruikers treft",
  "final_translation": "We hebben een kritiek incident dat meerdere gebruikers treft
  "source_language": "en",
  "enable_post_editor": false,
  "use_custom_category": true
}
```

**Response:**
```json
{
  "raw_translation": "We hebben een critical incident in de service desk",
  "enforced_translation": "We hebben een kritiek incident in de servicedesk",
  "final_translation": "We hebben een kritiek incident in de servicedesk",
  "post_edited": false,
  "applied_terms": [
    {
      "source_term": "critical incident",
      "target_term": "kritiek incident",
      "original_text": "critical incident",
      "position": 14
    },
    {
      "source_term": "service desk",
      "target_term": "servicedesk",
      "original_text": "service desk",
      "position": 43
    }
  ],
  "source_language": "en",
  "target_language": "nl",
  "detected_language": "en",
  "category_used": "your_category_id"
}
```

### `GET /api/languages`

Get supported languages.

### `GET /api/health`

Health check and configuration status.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_enforcer.py -v

# Run specific test
pytest tests/test_enforcer.py::TestTerminologyEnforcer::test_case_preservation_uppercase -v
```

## 🔧 Azure Setup Guide

### Azure Translator Text v3

1. **Create Translator Resource**
   - Azure Portal → Create Resource → Translator
   - Note: Key, Endpoint, Region

2. **Custom Translator (Optional)**
   - Visit: https://portal.customtranslator.azure.ai/
   - Create workspace → Create project
   - Upload parallel training data (source + Dutch)
   - Train model → Get category ID
   - Add category ID to `.env`

### Azure OpenAI (Optional)

1. **Create Azure OpenAI Resource**
   - Azure Portal → Create Resource → Azure OpenAI
   - Note: Endpoint, Key

2. **Deploy Model**
   - Azure OpenAI Studio → Deployments
   - Deploy GPT-4 or GPT-3.5-turbo
   - Note deployment name

3. **Configure**
   - Set `ENABLE_POST_EDITOR=true` in `.env`
   - Add endpoint, key, deployment name

## 📁 Project Structure

```
.
├── src/
│   ├── app.py                  # FastAPI application
│   ├── config/
│   │   ├── env.py              # Environment configuration
│   │   └── languages.py        # Supported languages
│   ├── services/
│   │   ├── translator.py       # Azure Translator client
│   │   └── post_editor.py      # Azure OpenAI post-editor
│   ├── terminology/
│   │   ├── glossary_loader.py  # TSV parser
│   │   ├── enforcer.py         # Term enforcement engine
│   │   └── audit.py            # Audit tracking
│   ├── routes/
│   │   └── translate.py        # API routes
│   └── ui/
│       └── templates/
│           └── index.html      # Web interface
├── tests/
│   ├── conftest.py
│   └── test_enforcer.py        # Enforcer unit tests
├── data/
│   └── glossary.tsv            # Terminology glossary
├── requirements.txt
├── .env.example
└── README.md
```

## ⚙️ How It Works

### Translation Pipeline

```
User Input (any language)
    ↓
Azure Translator Text v3
    ├─→ Uses custom category if configured
    └─→ allowFallback=false for consistency
    ↓
Raw Translation (Dutch)
    ↓
Glossary Enforcer
    ├─→ Loads TSV glossary
    ├─→ Sorts terms longest-first
    ├─→ Regex-based matching with word boundaries
    ├─→ Case preservation (UPPER, Title, lower)
    └─→ Audit tracking
    ↓
Enforced Translation (Dutch with correct terms)
    ↓
[Optional] Azure OpenAI Post-Editor
    ├─→ System prompt: "Never change glossary terms"
    ├─→ Protected terms list provided
    ├─→ Low temperature (0.3) for consistency
    └─→ Validation: term count check
    ↓
Final Translation (Fluent Dutch with enforced terms)
```

### Glossary Enforcement Strategy

**Key Challenges:**
1. **Overlapping terms** - "incident" vs "critical incident"
2. **Case variations** - "Problem", "PROBLEM", "problem"
3. **Partial matches** - "incident" in "incidental"

**Solution:**
```python
# 1. Sort by length (longest first)
glossary.sort(key=lambda e: len(e.source), reverse=True)

# 2. Word boundary detection
pattern = r'(?<!\w)' + escaped_term + r'(?!\w)'

# 3. Case preservation
if original.isupper():
    return replacement.upper()
elif original[0].isupper():
    return replacement.title()
else:
    return replacement.lower()
```

### ServiceNow Integration Example (Contoso Corp)

**Scenario:** Translate customer support ticket descriptions in real-time as they arrive in ServiceNow

**ServiceNow Workflow:**
```
1. Customer submits ticket in English
2. ServiceNow triggers REST API call to translation service
3. Service returns translated text with guaranteed terminology
4. Translation automatically updates ticket description
5. Support team works with consistently-translated tickets
```

**ServiceNow Integration Code (REST API Call):**
```javascript
// In ServiceNow Business Rule or Flow Designer
var request = new XMLHttpRequest();
var payload = {
  "text": incident.short_description,  // Original English text
  "source_language": "en",
  "enable_post_editor": false,
  "use_custom_category": true
};

request.open('POST', 'https://your-service.azurewebsites.net/api/translate', true);
request.setRequestHeader('Content-Type', 'application/json');
request.onload = function() {
  var response = JSON.parse(request.responseText);
  
  // Use the enforced translation with guaranteed terms
  incident.description = response.enforced_translation;
  incident.setWorkflow(false);
  incident.update();
  
  // Log which terms were applied
  gs.log('Applied terms: ' + JSON.stringify(response.applied_terms));
};
request.send(JSON.stringify(payload));
```

**Result for Contoso:**
- All incoming tickets translated consistently
- "critical incident" always becomes "incident"
- "service desk" always becomes "servicedesk"
- Support team immediately sees correct terminology
- Audit trail available for compliance

---

## 🎨 UI Features

- **Source Language Selection** - 6 supported languages
- **Post-Editor Toggle** - Enable/disable Azure OpenAI
- **Three-Panel Output**:
  - Raw translation (direct from Azure)
  - Enforced translation (with glossary applied, terms highlighted)
  - Final translation (post-edited if enabled)
- **Applied Terms List** - Shows all replacements with positions
- **Visual Diff** - Highlights enforced terms in yellow

## 🔒 Security Notes

- Never commit `.env` file (listed in `.gitignore`)
- Use Azure Managed Identity in production
- Implement rate limiting for public deployments
- Validate all user inputs
- Keep Azure keys rotated regularly

## 📈 Performance

**Typical Latency (measured):**
- Azure Translator: ~300-500ms
- Glossary Enforcement: ~10-50ms
- Azure OpenAI Post-Edit: ~1000-2000ms
- **Total (without post-edit):** < 1s
- **Total (with post-edit):** ~2s

**Optimization Tips:**
- Cache glossary entries in memory (done)
- Use connection pooling (httpx AsyncClient)
- Batch multiple translations in single request
- Consider Azure CDN for static assets

## � Learn More

### Understanding the Problem & Solution

Before implementing, it's helpful to understand the architectural challenge this solution addresses:

- **[Problem Statement Analysis](docs/PROBLEM_STATEMENT_ANALYSIS.md)** - In-depth analysis of:
  - Why real-time translation with guaranteed terminology consistency is challenging
  - How this service implements a two-layer enforcement mechanism
  - Performance characteristics and deployment options
  - Suitability assessment for different use cases

This analysis includes the Contoso Corp case study showing how organizations can translate real-time support tickets while maintaining strict terminology consistency.

## �� Troubleshooting

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

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📧 Support

For issues and questions:
- GitHub Issues: [Create an issue](../../issues)
- Azure Translator Docs: https://docs.microsoft.com/azure/cognitive-services/translator/
- Azure OpenAI Docs: https://learn.microsoft.com/azure/ai-services/openai/

---

Built with ❤️ using FastAPI, Azure Translator, and Azure OpenAI
