"""Azure Translator API Preview client with LLM support."""

import httpx
from typing import Optional, Dict, Any
from ..config.env import get_settings


class TranslatorPreviewClient:
    """Client for new Translator API preview with LLM capabilities."""
    
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
        model: str = "gpt-4o-mini",
        tone: str = "neutral",
        allow_fallback: bool = True
    ) -> Dict[str, Any]:
        """Translate text using preview API with optional LLM.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            enable_llm: Enable LLM enhancement
            model: LLM model to use (gpt-4o-mini or gpt-4o)
            tone: Translation tone (neutral, formal, informal, technical)
            allow_fallback: Fall back to standard if preview fails
            
        Returns:
            Dictionary with translation and metadata
        """
        try:
            url = f"{self.endpoint}/translator/text/batch/document"
            
            headers = {
                "Ocp-Apim-Subscription-Key": self.key,
                "Ocp-Apim-Subscription-Region": self.location,
                "Content-Type": "application/json"
            }
            
            # Build request payload for preview API
            payload = {
                "inputs": [
                    {
                        "source": {
                            "language": source_language,
                            "text": text
                        },
                        "targets": [
                            {
                                "language": target_language,
                                "settings": self._build_settings(enable_llm, model, tone)
                            }
                        ]
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
                    'model': model if enable_llm else None,
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
    
    def _build_settings(self, enable_llm: bool, model: str, tone: str) -> Dict[str, Any]:
        """Build translation settings for preview API.
        
        Args:
            enable_llm: Enable LLM enhancement
            model: LLM model name
            tone: Translation tone
            
        Returns:
            Settings dictionary
        """
        settings = {
            "tone": tone
        }
        
        if enable_llm:
            settings["llm"] = {
                "model": model,
                "temperature": 0.3  # Low temperature for consistency
            }
        
        return settings
    
    def _extract_translation(self, response: Dict[str, Any]) -> str:
        """Extract translated text from preview API response.
        
        Args:
            response: API response
            
        Returns:
            Translated text
        """
        try:
            # Navigate the response structure
            if "results" in response:
                results = response["results"]
                if results and len(results) > 0:
                    translations = results[0].get("translations", [])
                    if translations and len(translations) > 0:
                        text = translations[0].get("text", "")
                        return text
            
            # Fallback to direct text field
            return response.get("text", "")
        except (KeyError, IndexError, TypeError):
            return ""
    
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
