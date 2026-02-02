"""Azure OpenAI post-editor for fluency improvements."""

import json
from typing import Optional, List
import httpx
from ..config.env import get_settings


class PostEditor:
    """Post-editor using Azure OpenAI for fluency improvements.
    
    CRITICAL: The post-editor MUST NOT modify any glossary terms.
    This is enforced via system prompt.
    """
    
    SYSTEM_PROMPT = """You are a post-editor for Dutch translations. Your task is to improve the fluency and naturalness of machine-translated Dutch text while following these STRICT RULES:

1. DO NOT change ANY words from the DO_NOT_CHANGE list (glossary terms)
2. DO NOT alter any proper nouns, product names, or domain-specific vocabulary  
3. ONLY improve:
   - Grammar and syntax
   - Word order for naturalness
   - Article usage (de/het)
   - Minor phrasing to sound more native
4. Maintain the exact meaning and all key terms
5. If the text is already good, return it unchanged

CRITICAL: Terms in the DO_NOT_CHANGE list are domain-specific jargon and MUST remain exactly as provided.

Return ONLY the improved Dutch text, nothing else."""
    
    def __init__(self):
        """Initialize post-editor with settings."""
        self.settings = get_settings()
        
        if not self.settings.enable_post_editor:
            raise ValueError("Post-editor is not enabled in configuration")
        
        if not self.settings.azure_openai_endpoint or not self.settings.azure_openai_key:
            raise ValueError("Azure OpenAI configuration is incomplete")
        
        self.endpoint = self.settings.azure_openai_endpoint.rstrip('/')
        self.api_key = self.settings.azure_openai_key
        self.deployment = self.settings.azure_openai_deployment
        self.api_version = self.settings.azure_openai_api_version
    
    async def post_edit(
        self,
        text: str,
        protected_terms: Optional[List[str]] = None
    ) -> str:
        """Post-edit translated text for improved fluency.
        
        Args:
            text: Translated text to improve
            protected_terms: List of terms that must not be changed
            
        Returns:
            Post-edited text
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        # Build user prompt with protected terms as DO_NOT_CHANGE list
        user_prompt = text
        if protected_terms:
            terms_list = ", ".join(f'"{term}"' for term in protected_terms)
            user_prompt = (
                f"DO_NOT_CHANGE list (preserve exactly): {terms_list}\n\n"
                f"Text to improve:\n{text}"
            )
        
        # Build API request
        url = (
            f"{self.endpoint}/openai/deployments/{self.deployment}"
            f"/chat/completions?api-version={self.api_version}"
        )
        
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.api_key
        }
        
        body = {
            'messages': [
                {'role': 'system', 'content': self.SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.3,  # Low temperature for consistency
            'max_tokens': 2000,
            'top_p': 0.95
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=body,
                timeout=60.0
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the post-edited text
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0].get('message', {})
                content = message.get('content', '').strip()
                return content
            
            raise ValueError("Unexpected response format from Azure OpenAI")
    
    def is_available(self) -> bool:
        """Check if post-editor is available and configured.
        
        Returns:
            True if post-editor can be used, False otherwise
        """
        return (
            self.settings.enable_post_editor
            and bool(self.settings.azure_openai_endpoint)
            and bool(self.settings.azure_openai_key)
        )
    
    async def validate_term_preservation(
        self,
        original: str,
        edited: str,
        terms: List[str]
    ) -> tuple[bool, List[str]]:
        """Validate that protected terms were preserved.
        
        Args:
            original: Original text before post-editing
            edited: Post-edited text
            terms: List of protected terms
            
        Returns:
            Tuple of (all_preserved, list_of_changed_terms)
        """
        changed_terms = []
        
        for term in terms:
            # Check if term appears same number of times in both
            original_count = original.lower().count(term.lower())
            edited_count = edited.lower().count(term.lower())
            
            if original_count != edited_count:
                changed_terms.append(term)
        
        return (len(changed_terms) == 0, changed_terms)
