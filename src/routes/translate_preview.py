"""Preview translation API routes with LLM support."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..config.env import get_settings
from ..config.languages import SUPPORTED_LANGUAGES, is_supported
from ..services.translator_preview import get_preview_translator
from ..services.post_editor import PostEditor
from ..terminology.glossary_loader import GlossaryLoader
from ..terminology.enforcer import TerminologyEnforcer
from ..terminology.audit import EnforcementAudit


router = APIRouter(prefix="/api/preview", tags=["preview-translation"])

# Global instances (initialized on startup)
preview_translator = None
post_editor: Optional[PostEditor] = None
glossary_loader: Optional[GlossaryLoader] = None
terminology_enforcer: Optional[TerminologyEnforcer] = None


class PreviewTranslateRequest(BaseModel):
    """Request model for preview translation."""
    
    text: str = Field(..., description="Text to translate", min_length=1, max_length=10000)
    source_language: str = Field(..., description="Source language code")
    enable_llm: bool = Field(
        default=True,
        description="Enable LLM enhancement for fluency"
    )
    deployment_name: Optional[str] = Field(
        default=None,
        description="GPT-4o-mini deployment name from Foundry"
    )
    tone: str = Field(
        default="neutral",
        description="Translation tone: neutral, formal, informal, technical"
    )
    enforce_glossary: bool = Field(
        default=True,
        description="Apply glossary enforcement"
    )
    enable_post_editor: bool = Field(
        default=False,
        description="Enable post-editing for further fluency"
    )


class PreviewTranslateResponse(BaseModel):
    """Response model for preview translation."""
    
    raw_translation: str
    enforced_translation: Optional[str] = None
    final_translation: str
    post_edited: bool
    applied_terms: List[dict] = []
    source_language: str
    target_language: str
    method: str = "preview"
    llm_used: bool
    deployment_name: Optional[str] = None
    tone: str
    available: bool = True


def initialize_preview_services(
    post_editor_instance: Optional[PostEditor],
    glossary_loader_instance: Optional[GlossaryLoader],
    enforcer_instance: Optional[TerminologyEnforcer]
):
    """Initialize preview translation services.
    
    Args:
        post_editor_instance: Post-editor service
        glossary_loader_instance: Glossary loader service
        enforcer_instance: Terminology enforcer service
    """
    global preview_translator, post_editor, glossary_loader, terminology_enforcer
    
    preview_translator = get_preview_translator()
    post_editor = post_editor_instance
    glossary_loader = glossary_loader_instance
    terminology_enforcer = enforcer_instance


@router.post("/translate", response_model=PreviewTranslateResponse)
async def translate_preview(request: PreviewTranslateRequest):
    """Translate using preview API with optional LLM enhancement.
    
    Steps:
    1. Optional glossary masking
    2. Preview Translator API with LLM
    3. Optional glossary enforcement
    4. Optional post-editing
    """
    # Check if preview translator is available
    if not preview_translator:
        raise HTTPException(
            status_code=503,
            detail="Preview translator not configured. Configure TRANSLATOR_API_PREVIEW_* environment variables."
        )
    
    # Validate language
    if not is_supported(request.source_language):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported source language: {request.source_language}"
        )
    
    try:
        settings = get_settings()
        target_language = settings.target_language

        if request.enable_llm and not request.deployment_name:
            raise HTTPException(
                status_code=400,
                detail="deployment_name is required when enable_llm is true."
            )
        # Step 1: Optional glossary enforcement
        applied_terms = []
        text_to_translate = request.text
        
        if request.enforce_glossary and glossary_loader:
            # Mask glossary terms before translation
            import re
            masked_text = request.text
            placeholder_map = {}
            placeholder_idx = 0
            
            applicable_terms = terminology_enforcer.get_applicable_terms(request.text)
            sorted_terms = sorted(applicable_terms, key=lambda e: len(e.source), reverse=True)
            
            for entry in sorted_terms:
                pattern = re.compile(r'\b' + re.escape(entry.source) + r'\b', re.IGNORECASE)
                matches = list(pattern.finditer(masked_text))
                
                for match in reversed(matches):
                    placeholder = f"__GLOSS_{placeholder_idx}__"
                    placeholder_map[placeholder] = {
                        'target_term': entry.target,
                        'source_term': entry.source,
                        'original_case': match.group(0)
                    }
                    
                    start, end = match.span()
                    masked_text = masked_text[:start] + placeholder + masked_text[end:]
                    placeholder_idx += 1
            
            text_to_translate = masked_text
        
        # Step 2: Translate with preview API and optional LLM
        translation_result = await preview_translator.translate(
            text=text_to_translate,
            source_language=request.source_language,
            target_language=target_language,
            enable_llm=request.enable_llm,
            deployment_name=request.deployment_name,
            tone=request.tone,
            allow_fallback=True
        )
        
        raw_translation = translation_result.get('translated_text', '')
        
        # Step 3: Replace placeholders with glossary terms
        enforced_translation = raw_translation
        if request.enforce_glossary and 'placeholder_map' in locals():
            audit = EnforcementAudit(
                original_text=raw_translation,
                enforced_text=""
            )
            
            for placeholder, info in placeholder_map.items():
                if placeholder in enforced_translation:
                    target_term = info['target_term']
                    original_case = info['original_case']
                    
                    # Preserve case
                    if original_case.isupper():
                        replacement = target_term.upper()
                    elif original_case and original_case[0].isupper():
                        replacement = target_term[0].upper() + target_term[1:] if len(target_term) > 1 else target_term.upper()
                    else:
                        replacement = target_term.lower()
                    
                    placeholder_pos = enforced_translation.find(placeholder)
                    enforced_translation = enforced_translation.replace(placeholder, replacement)
                    
                    applied_terms.append({
                        'source_term': info['source_term'],
                        'target_term': target_term,
                        'original_text': placeholder,
                        'position': placeholder_pos
                    })
        
        # Step 4: Optional post-editing
        final_translation = enforced_translation if enforced_translation else raw_translation
        post_edited = False
        
        if request.enable_post_editor and post_editor and post_editor.is_available():
            protected_terms = [term['target_term'] for term in applied_terms]
            
            final_translation = await post_editor.post_edit(
                final_translation,
                protected_terms=protected_terms
            )
            
            preserved, _ = await post_editor.validate_term_preservation(
                final_translation if enforced_translation else raw_translation,
                final_translation,
                protected_terms
            )
            
            if preserved:
                post_edited = True
            else:
                final_translation = enforced_translation if enforced_translation else raw_translation
        
        # Build response
        return PreviewTranslateResponse(
            raw_translation=raw_translation,
            enforced_translation=enforced_translation if enforced_translation != raw_translation else None,
            final_translation=final_translation,
            post_edited=post_edited,
            applied_terms=applied_terms,
            source_language=request.source_language,
            target_language=target_language,
            llm_used=request.enable_llm,
            deployment_name=request.deployment_name if request.enable_llm else None,
            tone=request.tone,
            available=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Preview translation failed: {str(e)}"
        )


@router.get("/available")
async def check_availability():
    """Check if preview translator is available."""
    return {
        "available": preview_translator is not None,
        "configured": preview_translator is not None
    }
