# Translation Service Architecture

## Overview

The ACTION translation service implements a **multi-stage pipeline** for translating multi-language text to Dutch while preserving domain-specific terminology (ACTION retail jargon).

## Architecture (As Implemented)

### Current Implementation: Term Masking Approach

```
Source Text (EN/DE/FR/PL/ES/IT)
    ↓
[1] Glossary Term Detection & Masking
    Replace: "service desk" → "__GLOSS_0__"
    ↓
[2] Azure Translator Text v3 (NMT)
    Translate masked text
    ↓
[3] Term Replacement
    Replace: "__GLOSS_0__" → "servicedesk"
    ↓
[4] Optional: LLM Post-Editor (gpt-4o-mini)
    Improve fluency (DO_NOT_CHANGE list protected)
    ↓
Final Translation (NL) with guaranteed terminology
```

### Production-Ready Architecture (Recommended)

```
Source Text
    ↓
[1] Azure Translator Text v3 with Custom Translator
    - Use category parameter: &category={CUSTOM_MODEL_ID}
    - Set allowFallback=false for deterministic behavior
    - Custom Translator enforces glossary via trained model
    ↓
[2] Post-Processing Enforcer (Auditable Proof)
    - Regex-based replacement as safety net
    - Generates audit trail of term applications
    ↓
[3] Optional: LLM Post-Editor (gpt-4o-mini or gpt-4o)
    - Improve fluency without changing glossary terms
    - DO_NOT_CHANGE list in prompt
    ↓
Final Translation
```

## Stage Descriptions

### Stage 1: Term Masking (PoC) or Custom Translator (Production)

**PoC Approach (Current):**
- Pre-process source text to find all glossary terms
- Replace each term with unique placeholder (`__GLOSS_N__`)
- Maintains term positions for later replacement
- **Pros:** Works without Custom Translator setup
- **Cons:** Placeholders may affect translation context

**Production Approach (Recommended):**
- Upload glossary TSV to Azure Custom Translator
- Train custom model with phrase/sentence dictionaries
- Use `category` parameter in API calls
- **Pros:** Native Azure support, context-aware, lowest latency
- **Cons:** Requires Custom Translator project setup

### Stage 2: Azure Translator Text v3 (NMT)

**Endpoint:**
```
https://api.cognitive.microsofttranslator.com/translate
  ?api-version=3.0
  &from={source_lang}
  &to=nl
  &category={CATEGORY_ID}      # Optional: Custom Translator model
  &allowFallback=false           # Enforce custom model (don't fall back to generic)
```

**Headers:**
- `Ocp-Apim-Subscription-Key`: Azure Translator API key
- `Ocp-Apim-Subscription-Region`: westeurope
- `Content-Type`: application/json

**Features:**
- Supports 100+ source languages
- Low latency (~200-500ms)
- Deterministic with Custom Translator
- Production SLA available

### Stage 3: Terminology Enforcer (Post-Processing)

**Purpose:** Auditable proof layer + safety net

**Algorithm:**
1. Load glossary entries (source → target)
2. Search translated text for terms (case-insensitive, word boundaries)
3. Replace with glossary terms (preserve case pattern)
4. Track all replacements in audit log

**Case Preservation:**
- `Service Desk` → `Servicedesk`
- `service desk` → `servicedesk`
- `SERVICE DESK` → `SERVICEDESK`

**Regex Pattern:**
```python
pattern = r'\b' + re.escape(term) + r'\b'
re.finditer(pattern, text, re.IGNORECASE)
```

### Stage 4: LLM Post-Editor (Optional)

**Model Selection:**
- **Default:** `gpt-4o-mini` - Best speed/cost balance
- **Quality Demo:** `gpt-4o` - Higher quality, more expensive/slower

**System Prompt:**
```
You are a post-editor for Dutch translations.
Rules:
1. DO NOT change ANY words from the DO_NOT_CHANGE list (glossary terms)
2. ONLY improve grammar, syntax, word order, articles
3. If already good, return unchanged
```

**User Prompt:**
```
DO_NOT_CHANGE list: "servicedesk", "kassa", "filiaalbeheerder"

Text to improve:
{translated_text}
```

**Validation:**
- After LLM response: verify all glossary terms still present
- If any term changed: revert to pre-LLM version
- Log warnings for debugging

## Configuration

### Environment Variables

```bash
# Azure Translator (Required)
AZURE_TRANSLATOR_KEY=<your-key>
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com/
AZURE_TRANSLATOR_REGION=westeurope
AZURE_TRANSLATOR_CATEGORY=         # Custom Translator model ID (optional)

# Translation Settings
TARGET_LANGUAGE=nl
GLOSSARY_PATH=data/glossary.tsv

# Azure OpenAI (Optional)
ENABLE_POST_EDITOR=false
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_KEY=
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### Glossary Format (TSV)

```
EN              NL
service desk    servicedesk
Service desk    Servicedesk
Service Desk    Servicedesk
customer        klant
cash register   kassa
store manager   filiaalbeheerder
```

**Rules:**
- Tab-separated values
- Column 1: Source term (any language)
- Column 2: Target term (Dutch)
- Multiple case variations for better matching
- Sorted by length (longest first) for overlap handling

## API Endpoints

### POST /api/translate

**Request:**
```json
{
  "text": "Please contact the service desk for help.",
  "source_language": "en",
  "enable_post_editor": false,
  "use_custom_category": true
}
```

**Response:**
```json
{
  "raw_translation": "Neem contact op met de __GLOSS_0__ voor hulp.",
  "enforced_translation": "Neem contact op met de servicedesk voor hulp.",
  "final_translation": "Neem contact op met de servicedesk voor hulp.",
  "post_edited": false,
  "applied_terms": [
    {
      "source_term": "service desk",
      "target_term": "servicedesk",
      "original_text": "__GLOSS_0__",
      "position": 23
    }
  ],
  "source_language": "en",
  "target_language": "nl",
  "detected_language": null,
  "category_used": ""
}
```

### GET /api/health

**Response:**
```json
{
  "status": "healthy",
  "translator_configured": true,
  "glossary_loaded": true,
  "glossary_terms": 204,
  "post_editor_enabled": false,
  "post_editor_available": false
}
```

### GET /api/languages

**Response:**
```json
{
  "supported_languages": {
    "de": "German",
    "fr": "French",
    "pl": "Polish",
    "es": "Spanish",
    "it": "Italian",
    "en": "English"
  },
  "target_language": "nl"
}
```

## Performance Characteristics

### PoC (Term Masking)
- **Latency:** ~300-600ms per request
- **Throughput:** ~50 requests/min (B1 tier)
- **Determinism:** 100% (terms always enforced)
- **Context Quality:** May be affected by placeholders

### Production (Custom Translator)
- **Latency:** ~200-400ms per request
- **Throughput:** ~100 requests/min (S1 tier)
- **Determinism:** ~95-98% (model-dependent)
- **Context Quality:** Excellent (native support)

### With LLM Post-Editor
- **Additional Latency:** +1-3 seconds (gpt-4o-mini)
- **Cost:** ~$0.15 per 1M input tokens
- **Quality Improvement:** Noticeable for fluency
- **Risk:** May change terminology (mitigated by validation)

## Migration Path: PoC → Production

### Step 1: Current PoC (✅ Implemented)
- Term masking for deterministic enforcement
- Works immediately without Custom Translator
- Good for demo and testing

### Step 2: Custom Translator Setup
1. Create Custom Translator project in Azure Portal
2. Upload glossary TSV as dictionary
3. Optionally add parallel sentence pairs for context
4. Train model (~6-24 hours)
5. Get category ID

### Step 3: Update Configuration
```bash
AZURE_TRANSLATOR_CATEGORY=<your-category-id>
```

### Step 4: A/B Testing
- Run both approaches in parallel
- Compare quality and consistency
- Measure latency difference
- Validate terminology enforcement

### Step 5: Switch to Production
- Disable term masking (or keep as safety net)
- Use Custom Translator as primary enforcement
- Keep post-processing enforcer for audit trail

## Security & Compliance

### Data Handling
- No data stored by translation service
- All requests processed in-memory
- Audit logs contain only metadata (not full text)

### API Keys
- Stored in environment variables / Azure Key Vault
- Never logged or exposed in responses
- Rotated according to security policy

### Azure Services
- All within same Azure tenant
- Managed Identity support (planned)
- Private endpoints available (planned)
- Application Insights for monitoring

## Testing

### Local Testing
```bash
# Start server
source venv/bin/activate
python run.py

# Test API
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text":"Contact the service desk","source_language":"en"}'
```

### Unit Tests
```bash
pytest tests/unit -v
```

### Integration Tests
```bash
pytest tests/integration -v --env=dev
```

## Monitoring & Observability

### Application Insights Metrics
- Request duration (percentiles)
- Error rates
- Glossary term application count
- LLM post-editor usage

### Custom Metrics
- Terms enforced per request
- Average placeholder count
- Translation quality scores
- API call duration by stage

### Alerts
- High error rate (>5%)
- Slow response time (>2s)
- Azure Translator API failures
- LLM validation failures

## Known Limitations

### Term Masking Approach
1. **Context Loss:** Placeholders may reduce translation quality
2. **Compound Terms:** "action cash register" may split incorrectly
3. **Scalability:** Large glossaries (>1000 terms) slow down pre-processing

### Custom Translator Approach
1. **Setup Time:** Requires model training (6-24 hours)
2. **Not 100% Deterministic:** ML model may vary slightly
3. **Cost:** Additional Azure resource required

### LLM Post-Editor
1. **Latency:** Adds 1-3 seconds per request
2. **Non-Determinism:** Same input may produce different outputs
3. **Cost:** Higher than NMT alone
4. **Risk:** May change protected terms (validation mitigates this)

## Recommendations

### For PoC/Demo
✅ Use current term masking implementation
✅ Disable LLM post-editor (lower latency)
✅ Focus on terminology enforcement demo

### For Production
1. Set up Custom Translator with glossary
2. Use `category` parameter with `allowFallback=false`
3. Keep post-processing enforcer as audit trail
4. Enable LLM post-editor only for high-value content
5. Use gpt-4o-mini as default (gpt-4o for quality showcase)
6. Monitor terminology preservation rate
7. Implement caching for repeated phrases

### For ACTION Retail
- Upload complete ACTION glossary to Custom Translator
- Include store operations, customer service, training terminology
- Train with parallel ServiceNow ticket examples
- Test with real ticket data before deployment
- Monitor enforcement rate and collect feedback
