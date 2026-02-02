"""Azure Translator Text v3 API client."""

import httpx
from typing import Optional, List, Dict
from ..config.env import get_settings


class TranslatorClient:
    """Client for Azure Translator Text v3 API."""
    
    def __init__(self):
        """Initialize translator client with settings."""
        self.settings = get_settings()
        self.base_url = self.settings.azure_translator_endpoint.rstrip('/')
        self.headers = {
            'Ocp-Apim-Subscription-Key': self.settings.azure_translator_key,
            'Ocp-Apim-Subscription-Region': self.settings.azure_translator_region,
            'Content-Type': 'application/json'
        }
    
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: Optional[str] = None,
        use_custom_category: bool = True,
        allow_fallback: bool = False
    ) -> Dict:
        """Translate text using Azure Translator Text v3 API.
        
        Args:
            text: Text to translate
            source_language: Source language code (e.g., 'de', 'fr')
            target_language: Target language code (defaults to settings)
            use_custom_category: Whether to use custom translator category
            allow_fallback: Whether to allow fallback to default translation
            
        Returns:
            Dictionary with translation result
            
        Raises:
            httpx.HTTPError: If translation request fails
        """
        if target_language is None:
            target_language = self.settings.target_language
        
        # Build API endpoint
        endpoint = f"{self.base_url}/translate"
        
        # Build query parameters
        params = {
            'api-version': '3.0',
            'from': source_language,
            'to': target_language,
        }
        
        # Add custom category if configured and requested
        if use_custom_category and self.settings.azure_translator_category:
            params['category'] = self.settings.azure_translator_category
            if not allow_fallback:
                params['allowFallback'] = 'false'
        
        # Build request body
        body = [{'text': text}]
        
        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                params=params,
                headers=self.headers,
                json=body,
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract translation from response
            if result and len(result) > 0:
                translation_result = result[0]
                if 'translations' in translation_result and translation_result['translations']:
                    translated_text = translation_result['translations'][0]['text']
                    detected_language = translation_result.get('detectedLanguage', {})
                    
                    return {
                        'translated_text': translated_text,
                        'source_language': source_language,
                        'target_language': target_language,
                        'detected_language': detected_language.get('language'),
                        'detection_score': detected_language.get('score'),
                        'category_used': self.settings.azure_translator_category if use_custom_category else None
                    }
            
            raise ValueError("Unexpected response format from Azure Translator")
    
    async def detect_language(self, text: str) -> Dict:
        """Detect language of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with detected language info
        """
        endpoint = f"{self.base_url}/detect"
        params = {'api-version': '3.0'}
        body = [{'text': text}]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                params=params,
                headers=self.headers,
                json=body,
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result and len(result) > 0:
                detection = result[0]
                return {
                    'language': detection.get('language'),
                    'score': detection.get('score'),
                    'is_translation_supported': detection.get('isTranslationSupported'),
                    'alternatives': detection.get('alternatives', [])
                }
            
            raise ValueError("Unexpected response format from language detection")
    
    async def get_supported_languages(self) -> Dict:
        """Get list of supported languages.
        
        Returns:
            Dictionary with supported languages
        """
        endpoint = f"{self.base_url}/languages"
        params = {'api-version': '3.0'}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                endpoint,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            
            return response.json()
