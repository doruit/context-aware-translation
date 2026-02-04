# API Reference Guide

Complete API documentation for the Azure Translation Service with Glossary Enforcement.

## Base URL

```
http://localhost:8000
```

In production, replace with your deployed URL (e.g., `https://your-service.azurewebsites.net`)

## Endpoints

### `POST /api/translate`

Translate text with glossary enforcement and optional post-editing.

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | The text to translate |
| `source_language` | string | Yes | Source language code (e.g., `en`, `de`, `fr`) |
| `enable_post_editor` | boolean | No | Enable Azure OpenAI post-editing (default: `false`) |
| `use_custom_category` | boolean | No | Use Custom Translator category if configured (default: `true`) |

**Supported Source Languages:**
- `en` - English
- `de` - German
- `fr` - French
- `pl` - Polish
- `es` - Spanish
- `it` - Italian

#### Example Request

```bash
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
  "text": "The service desk received a critical incident. The customer reports the cash register is not working. Store manager needs immediate help.",
  "source_language": "en",
  "enable_post_editor": false,
  "use_custom_category": true
}'
```

#### Response

**Status Code:** `200 OK`

**Body:**

```json
{
  "raw_translation": "De servicebalie ontving een kritiek voorval. De klant meldt dat de kassa niet werkt. Winkelbeheerder heeft onmiddellijke hulp nodig.",
  "enforced_translation": "De servicedesk ontving een incident. De klant meldt dat de kassa niet werkt. Filiaalbeheerder heeft onmiddellijke hulp nodig.",
  "final_translation": "De servicedesk ontving een incident. De klant meldt dat de kassa niet werkt. Filiaalbeheerder heeft onmiddellijke hulp nodig.",
  "post_edited": false,
  "applied_terms": [
    {
      "source_term": "service desk",
      "target_term": "servicedesk",
      "original_text": "service desk",
      "position": 4
    },
    {
      "source_term": "critical incident",
      "target_term": "incident",
      "original_text": "critical incident",
      "position": 35
    },
    {
      "source_term": "customer",
      "target_term": "klant",
      "original_text": "customer",
      "position": 58
    },
    {
      "source_term": "cash register",
      "target_term": "kassa",
      "original_text": "cash register",
      "position": 82
    },
    {
      "source_term": "store manager",
      "target_term": "filiaalbeheerder",
      "original_text": "Store manager",
      "position": 114
    }
  ],
  "source_language": "en",
  "target_language": "nl",
  "detected_language": "en",
  "category_used": "your_category_id"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `raw_translation` | string | Direct output from Azure Translator (before glossary enforcement) |
| `enforced_translation` | string | Translation after glossary terms are enforced |
| `final_translation` | string | Final output (same as enforced if post-editor disabled, or post-edited version) |
| `post_edited` | boolean | Whether Azure OpenAI post-editing was applied |
| `applied_terms` | array | List of glossary terms that were applied |
| `source_language` | string | Source language code used |
| `target_language` | string | Target language code (configured in `.env`) |
| `detected_language` | string | Language detected by Azure Translator |
| `category_used` | string | Custom Translator category ID used (if any) |

**Applied Terms Object:**

| Field | Type | Description |
|-------|------|-------------|
| `source_term` | string | Original glossary term (from TSV) |
| `target_term` | string | Target glossary term (from TSV) |
| `original_text` | string | Actual text found in translation (preserves case) |
| `position` | integer | Character position where term was found |

#### Error Responses

**400 Bad Request**
```json
{
  "detail": "Missing required field: text"
}
```

**401 Unauthorized**
```json
{
  "detail": "Azure Translator authentication failed"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Translation service error: [error message]"
}
```

---

### `GET /api/languages`

Get list of supported source languages.

#### Example Request

```bash
curl http://localhost:8000/api/languages
```

#### Response

**Status Code:** `200 OK`

```json
{
  "source_languages": [
    {
      "code": "en",
      "name": "English"
    },
    {
      "code": "de",
      "name": "German"
    },
    {
      "code": "fr",
      "name": "French"
    },
    {
      "code": "pl",
      "name": "Polish"
    },
    {
      "code": "es",
      "name": "Spanish"
    },
    {
      "code": "it",
      "name": "Italian"
    }
  ],
  "target_language": {
    "code": "nl",
    "name": "Dutch"
  }
}
```

---

### `GET /api/health`

Health check and configuration status.

#### Example Request

```bash
curl http://localhost:8000/api/health
```

#### Response

**Status Code:** `200 OK`

```json
{
  "status": "healthy",
  "translator_configured": true,
  "post_editor_enabled": false,
  "custom_category_configured": true,
  "glossary_terms_loaded": 42,
  "target_language": "nl"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Overall service status (`healthy` or `degraded`) |
| `translator_configured` | boolean | Whether Azure Translator credentials are valid |
| `post_editor_enabled` | boolean | Whether Azure OpenAI post-editor is enabled |
| `custom_category_configured` | boolean | Whether Custom Translator category is set |
| `glossary_terms_loaded` | integer | Number of terms loaded from glossary file |
| `target_language` | string | Configured target language code |

---

## ServiceNow Integration Example

For organizations using ServiceNow, here's how to integrate the translation service:

### ServiceNow Business Rule

**When:** Before insert  
**Table:** Incident  
**Condition:** `short_description` is not empty

```javascript
(function executeRule(current, previous) {
    try {
        // Only translate if not already in Dutch
        if (current.short_description && !isDutch(current.short_description)) {
            var translationResult = callTranslationService(
                current.short_description,
                detectLanguage(current.short_description)
            );
            
            // Use enforced translation (with guaranteed terminology)
            current.description = translationResult.enforced_translation;
            
            // Store original for reference
            current.work_notes = 'Original (' + translationResult.source_language + '): ' + 
                                 current.short_description;
            
            // Log applied terms for audit
            if (translationResult.applied_terms.length > 0) {
                gs.info('Glossary terms applied: ' + 
                       JSON.stringify(translationResult.applied_terms));
            }
        }
    } catch (e) {
        gs.error('Translation failed: ' + e.message);
        // Fallback: keep original text
    }
})(current, previous);

function callTranslationService(text, sourceLang) {
    var request = new sn_ws.RESTMessageV2();
    request.setEndpoint('https://your-service.azurewebsites.net/api/translate');
    request.setHttpMethod('POST');
    request.setRequestHeader('Content-Type', 'application/json');
    
    var payload = {
        text: text,
        source_language: sourceLang,
        enable_post_editor: false,  // Keep fast for real-time
        use_custom_category: true
    };
    
    request.setRequestBody(JSON.stringify(payload));
    
    var response = request.execute();
    if (response.getStatusCode() == 200) {
        return JSON.parse(response.getBody());
    } else {
        throw new Error('API returned ' + response.getStatusCode());
    }
}

function detectLanguage(text) {
    // Simple heuristic - implement proper detection or use Azure's language detection
    if (/^[a-zA-Z\s.,!?]+$/.test(text)) {
        return 'en';  // Default to English
    }
    return 'en';
}

function isDutch(text) {
    // Simple check - could be improved
    return /\b(de|het|een|van|is)\b/i.test(text.substring(0, 50));
}
```

### Integration Benefits

- ✅ All tickets translated consistently
- ✅ Guaranteed terminology enforcement
- ✅ < 1 second latency (users don't notice)
- ✅ Audit trail of applied terms
- ✅ Support team works in native language

---

## Python Client Example

```python
import requests
import json

class TranslationClient:
    def __init__(self, base_url):
        self.base_url = base_url
        
    def translate(self, text, source_language, enable_post_editor=False):
        """Translate text with glossary enforcement."""
        url = f"{self.base_url}/api/translate"
        payload = {
            "text": text,
            "source_language": source_language,
            "enable_post_editor": enable_post_editor,
            "use_custom_category": True
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_languages(self):
        """Get supported languages."""
        url = f"{self.base_url}/api/languages"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def health_check(self):
        """Check service health."""
        url = f"{self.base_url}/api/health"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

# Usage
client = TranslationClient("http://localhost:8000")

# Translate text
result = client.translate(
    text="Critical incident at service desk",
    source_language="en"
)

print(f"Raw: {result['raw_translation']}")
print(f"Enforced: {result['enforced_translation']}")
print(f"Applied terms: {len(result['applied_terms'])}")

# Get supported languages
languages = client.get_languages()
print(f"Supported languages: {languages['source_languages']}")

# Health check
health = client.health_check()
print(f"Service status: {health['status']}")
```

---

## Performance Characteristics

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

---

## Rate Limiting

Azure Translator has the following limits:

- **Free Tier (F0):** 2M characters/month
- **Standard Tier (S1):** Pay-as-you-go, 40 requests/second

Consider implementing rate limiting in your application if handling high traffic.

---

## Security Best Practices

- Never expose Azure keys in client-side code
- Use Azure Managed Identity in production
- Implement authentication/authorization for your API
- Validate and sanitize all user inputs
- Enable CORS only for trusted domains
- Use HTTPS in production
- Rotate Azure keys regularly

---

## Next Steps

- **[Azure Setup Guide](AZURE_SETUP.md)** - Configure Custom Translator and Azure OpenAI
- **[Quick Start](QUICKSTART.md)** - Get the service running
- **[Testing Guide](TESTING_GUIDE.md)** - Run tests and validate setup
- **[Main README](../README.md)** - Architecture and detailed documentation
