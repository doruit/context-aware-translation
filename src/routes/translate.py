"""Translation API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..config.env import get_settings
from ..config.languages import SUPPORTED_LANGUAGES, is_supported
from ..services.translator import TranslatorClient
from ..services.post_editor import PostEditor
from ..terminology.glossary_loader import GlossaryLoader
from ..terminology.enforcer import TerminologyEnforcer
from ..terminology.audit import EnforcementAudit


router = APIRouter(prefix="/api", tags=["translation"])

# Global instances (initialized on startup)
translator_client: Optional[TranslatorClient] = None
post_editor: Optional[PostEditor] = None
glossary_loader: Optional[GlossaryLoader] = None
terminology_enforcer: Optional[TerminologyEnforcer] = None


class TranslateRequest(BaseModel):
    """Request model for translation."""
    
    text: str = Field(..., description="Text to translate", min_length=1)
    source_language: str = Field(..., description="Source language code (e.g., 'de', 'fr')")
    enable_post_editor: bool = Field(
        default=False,
        description="Enable Azure OpenAI post-editing for fluency"
    )
    use_custom_category: bool = Field(
        default=True,
        description="Use custom translator category if configured"
    )


class TranslateResponse(BaseModel):
    """Response model for translation."""
    
    raw_translation: str = Field(..., description="Raw translation from Azure Translator")
    enforced_translation: str = Field(..., description="Translation with glossary terms enforced")
    final_translation: str = Field(..., description="Final translation (post-edited if enabled)")
    post_edited: bool = Field(..., description="Whether post-editing was applied")
    applied_terms: list = Field(..., description="List of glossary terms that were applied")
    source_language: str
    target_language: str
    detected_language: Optional[str] = None
    category_used: Optional[str] = None


@router.post("/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest) -> TranslateResponse:
    """Translate text with glossary enforcement.
    
    Pipeline:
    1. Translate using Azure Translator Text v3 (with optional custom category)
    2. Enforce glossary terms deterministically
    3. Optionally post-edit for fluency (without changing glossary terms)
    
    Args:
        request: Translation request
        
    Returns:
        Translation response with all pipeline stages
        
    Raises:
        HTTPException: If translation fails
    """
    # Validate source language
    if not is_supported(request.source_language):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported source language: {request.source_language}. "
                   f"Supported: {', '.join(SUPPORTED_LANGUAGES.keys())}"
        )
    
    try:
        # ARCHITECTURE NOTE:
        # - Primary enforcement SHOULD come from Azure Custom Translator (category parameter)
        # - For PoC without Custom Translator: use term masking to protect glossary terms
        # - Enforcer acts as auditable proof layer
        
        # Step 1: Identify glossary terms in source text and mask them
        import re
        source_terms_found = []
        masked_text = request.text
        placeholder_map = {}
        
        # Find all glossary terms in source text (longest first to avoid partial matches)
        applicable_terms = terminology_enforcer.get_applicable_terms(request.text)
        sorted_terms = sorted(applicable_terms, key=lambda e: len(e.source), reverse=True)
        
        placeholder_idx = 0
        for entry in sorted_terms:
            # Find all occurrences with word boundaries
            pattern = re.compile(r'\b' + re.escape(entry.source) + r'\b', re.IGNORECASE)
            matches = list(pattern.finditer(masked_text))
            
            for match in reversed(matches):  # Process in reverse to maintain positions
                placeholder = f"__GLOSS_{placeholder_idx}__"
                placeholder_map[placeholder] = {
                    'target_term': entry.target,
                    'source_term': entry.source,
                    'original_case': match.group(0)
                }
                
                # Replace term with placeholder
                start, end = match.span()
                masked_text = masked_text[:start] + placeholder + masked_text[end:]
                placeholder_idx += 1
                
                if entry not in source_terms_found:
                    source_terms_found.append(entry)
        
        # Step 2: Translate the masked text
        translation_result = await translator_client.translate(
            text=masked_text,
            source_language=request.source_language,
            use_custom_category=request.use_custom_category,
            allow_fallback=False
        )
        
        raw_translation = translation_result['translated_text']
        
        # Step 3: Replace placeholders with glossary target terms (preserving case)
        audit = EnforcementAudit(
            original_text=raw_translation,
            enforced_text=""
        )
        
        enforced_translation = raw_translation
        for placeholder, info in placeholder_map.items():
            if placeholder in enforced_translation:
                # Determine case preservation
                target_term = info['target_term']
                original_case = info['original_case']
                
                # Preserve case pattern
                if original_case.isupper():
                    replacement = target_term.upper()
                elif original_case[0].isupper() if original_case else False:
                    replacement = target_term[0].upper() + target_term[1:] if len(target_term) > 1 else target_term.upper()
                else:
                    replacement = target_term.lower()
                
                # Find placeholder position for audit
                placeholder_pos = enforced_translation.find(placeholder)
                
                # Replace placeholder with glossary term
                enforced_translation = enforced_translation.replace(placeholder, replacement)
                
                # Record in audit
                audit.add_application(
                    source_term=info['source_term'],
                    target_term=target_term,
                    position=placeholder_pos,
                    original_text=placeholder
                )
        
        audit.enforced_text = enforced_translation
        
        # Step 3: Optional post-editing
        final_translation = enforced_translation
        post_edited = False
        
        if request.enable_post_editor and post_editor and post_editor.is_available():
            # Get list of protected terms (terms that were applied)
            protected_terms = [app.target_term for app in audit.applied_terms]
            
            # Post-edit
            final_translation = await post_editor.post_edit(
                enforced_translation,
                protected_terms=protected_terms
            )
            post_edited = True
            
            # Validate that terms were preserved
            preserved, changed = await post_editor.validate_term_preservation(
                enforced_translation,
                final_translation,
                protected_terms
            )
            
            if not preserved:
                # Log warning but don't fail - use enforced version instead
                print(f"Warning: Post-editor changed protected terms: {changed}")
                final_translation = enforced_translation
                post_edited = False
        
        # Build response
        return TranslateResponse(
            raw_translation=raw_translation,
            enforced_translation=enforced_translation,
            final_translation=final_translation,
            post_edited=post_edited,
            applied_terms=audit.get_summary()['replacements'],
            source_language=request.source_language,
            target_language=translation_result['target_language'],
            detected_language=translation_result.get('detected_language'),
            category_used=translation_result.get('category_used')
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )


@router.get("/languages")
async def get_supported_languages():
    """Get list of supported source languages.
    
    Returns:
        Dictionary of supported language codes and names
    """
    return {
        "supported_languages": SUPPORTED_LANGUAGES,
        "target_language": get_settings().target_language
    }


@router.get("/health")
async def health_check():
    """Health check endpoint.
    
    Returns:
        Health status
    """
    settings = get_settings()
    
    return {
        "status": "healthy",
        "translator_configured": bool(settings.azure_translator_key),
        "glossary_loaded": bool(terminology_enforcer and terminology_enforcer.entries),
        "glossary_terms": len(terminology_enforcer.entries) if terminology_enforcer else 0,
        "post_editor_enabled": settings.enable_post_editor,
        "post_editor_available": post_editor.is_available() if post_editor else False
    }


def initialize_services():
    """Initialize global service instances.
    
    Should be called during application startup.
    """
    global translator_client, post_editor, glossary_loader, terminology_enforcer
    
    settings = get_settings()
    
    # Initialize translator
    translator_client = TranslatorClient()
    
    # Initialize post-editor if enabled
    if settings.enable_post_editor:
        try:
            post_editor = PostEditor()
        except Exception as e:
            print(f"Warning: Could not initialize post-editor: {e}")
            post_editor = None
    
    # Load glossary
    glossary_paths = settings.get_glossary_paths()
    glossary_loader = GlossaryLoader(glossary_paths)
    
    try:
        entries = glossary_loader.load()
        terminology_enforcer = TerminologyEnforcer(entries)
        print(f"Loaded {len(entries)} glossary terms from {glossary_paths}")
    except FileNotFoundError:
        print(f"Warning: Glossary file not found at {glossary_paths}")
        # Initialize with empty glossary
        terminology_enforcer = TerminologyEnforcer([])
    except Exception as e:
        print(f"Error loading glossary: {e}")
        terminology_enforcer = TerminologyEnforcer([])
