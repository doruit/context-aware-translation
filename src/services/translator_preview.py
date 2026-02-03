"""Azure Translator API Preview client with LLM support."""

import httpx
from typing import Optional, Dict, Any
from ..config.env import get_settings


class TranslatorPreviewClient:
    """Client for Translator API preview with GPT-4o-mini deployment support."""
    
    def __init__(self, key: str, endpoint: str, location: str):
        """Initialize preview translator client.
        
        Args:
            key: API key for preview translator
            endpoint: Endpoint URL
            location: Azure region location
        """
        self.key = key
        self.endpoint = endpoint
        self.location = location
        self.client = httpx.AsyncClient()
    
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str = "nl",
        enable_llm: bool = False,
        deployment_name: Optional[str] = None,
        tone: str = "neutral",
        allow_fallback: bool = True
    ) -> Dict[str, Any]:
        """Translate text using preview API with optional GPT-4o-mini deployment.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            enable_llm: Enable LLM enhancement (requires deployment_name)
            deployment_name: GPT-4o-mini deployment name from Foundry
            tone: Translation tone (neutral, formal, informal, technical)
            allow_fallback: Fall back to standard if preview fails
            
        Returns:
            Dictionary with translation and metadata
        """
        try:
            url = self._build_translate_url()
            
            headers = {
                "Ocp-Apim-Subscription-Key": self.key,
                "Ocp-Apim-Subscription-Region": self.location,
                "Content-Type": "application/json"
            }
            
            target_settings = self._build_target_settings(
                target_language=target_language,
                enable_llm=enable_llm,
                deployment_name=deployment_name,
                tone=tone,
                allow_fallback=allow_fallback
            )

            payload = {
                "inputs": [
                    {
                        "text": text,
                        "language": source_language,
                        "targets": [target_settings]
                    }
                ]
            }
            
            response = await self.client.post(
                url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                translated_text = self._extract_translation(result)
                return {
                    'translated_text': translated_text,
                    'source_language': source_language,
                    'target_language': target_language,
                    'method': 'preview',
                    'llm_used': enable_llm,
                    'deployment_name': deployment_name if enable_llm else None,
                    'tone': tone
                }
            else:
                raise Exception(f"Preview API error: {response.status_code}")
                
        except Exception as e:
            if allow_fallback:
                print(f"Preview translator failed, falling back: {str(e)}")
                return {
                    'translated_text': text,
                    'error': str(e),
                    'method': 'preview',
                    'fallback': True
                }
            raise
    
    def _build_target_settings(
        self,
        target_language: str,
        enable_llm: bool,
        deployment_name: Optional[str],
        tone: str,
        allow_fallback: bool
    ) -> Dict[str, Any]:
        """Build target settings for preview API.
        
        Args:
            enable_llm: Enable LLM enhancement
            deployment_name: GPT-4o-mini deployment name
            tone: Translation tone
            allow_fallback: Allow fallback to NMT
            
        Returns:
            Target settings dictionary
        """
        settings: Dict[str, Any] = {
            "language": target_language,
            "tone": tone,
            "allowFallback": allow_fallback
        }

        if enable_llm and deployment_name:
            settings["deploymentName"] = deployment_name

        return settings
    
    def _extract_translation(self, response: Dict[str, Any]) -> str:
        """Extract translated text from preview API response.
        
        Args:
            response: API response
            
        Returns:
            Translated text
        """
        try:
            value = response.get("value", [])
            if value:
                translations = value[0].get("translations", [])
                if translations:
                    return translations[0].get("text", "")
            return ""
        except (KeyError, IndexError, TypeError):
            return ""

    def _build_translate_url(self) -> str:
        """Build the preview translate endpoint URL."""
        api_version = "2025-10-01-preview"
        endpoint = self.endpoint.rstrip("/")

        if "/translate" in endpoint and "api-version=" in endpoint:
            return endpoint

        if "api.cognitive.microsofttranslator.com" in endpoint:
            return f"{endpoint}/translate?api-version={api_version}"

        if "/translator/text/translate" in endpoint:
            return f"{endpoint}?api-version={api_version}"

        return f"{endpoint}/translator/text/translate?api-version={api_version}"
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


def get_preview_translator() -> Optional[TranslatorPreviewClient]:
    """Get preview translator client if configured.
    
    Returns:
        TranslatorPreviewClient or None if not configured
    """
    settings = get_settings()
    
    if (settings.translator_api_preview_endpoint and 
        settings.translator_api_preview_key and
        settings.translator_api_preview_location):
        return TranslatorPreviewClient(
            key=settings.translator_api_preview_key,
            endpoint=settings.translator_api_preview_endpoint,
            location=settings.translator_api_preview_location
        )
    
    return None
