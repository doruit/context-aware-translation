# Glossary Enforcement - Implementation Note

## Problem Discovered

Azure Translator produces **context-dependent translations** for the same term:
- "service desk" (standalone) → "Servicedesk"  
- "service desk" (in sentence) → "servicebalie"

This makes post-translation glossary enforcement unreliable because we cannot predict what Azure will translate each term to in context.

## Solution Options

### Option 1: Azure Custom Translator (RECOMMENDED for Production)
Upload the glossary as a Custom Dictionary to Azure Translator:
- Create a Custom Translator project
- Upload TSV glossary as dictionary
- Train custom model
- Use custom category ID in translation requests

**Pros:**
- Native Azure support
- Consistent term handling
- No post-processing needed
- Handles context properly

**Cons:**
- Requires Custom Translator setup
- Takes time to train models
- Additional Azure resource

### Option 2: Pre-Translation Term Masking (Current Approach)
1. Before translation: Find glossary terms in source
2. Replace them with unique placeholders (`__TERM_1__`, etc.)
3. Translate the masked text
4. Replace placeholders with glossary target terms

**Pros:**
- Works with standard Translator API
- Deterministic term preservation
- No additional Azure resources

**Cons:**
- Placeholders may affect translation quality
- Complex masking logic needed

### Option 3: Smart Post-Processing with Multiple Translations
For each glossary term, get multiple translation candidates and search for all of them.

**Pros:**
- Works with standard API
- More robust than single translation lookup

**Cons:**
- Multiple API calls (slow, expensive)
- Still not 100% reliable

## Recommended Implementation

For this PoC, implement **Option 2 (Term Masking)** as it provides deterministic results without requiring Custom Translator setup.

For production use with ACTION, set up **Option 1 (Custom Translator)** for best results.

## Current Status

The current implementation attempts post-translation replacement but fails due to context-dependent translations. This needs to be refactored to use term masking.
