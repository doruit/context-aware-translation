"""Supported source languages for translation."""

from typing import Dict

# ISO 639-1 language codes supported as source languages
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "de": "German",
    "fr": "French",
    "pl": "Polish",
    "es": "Spanish",
    "it": "Italian",
    "en": "English",
}


def is_supported(language_code: str) -> bool:
    """Check if a language code is supported.
    
    Args:
        language_code: ISO 639-1 language code (e.g., 'de', 'fr')
        
    Returns:
        True if language is supported, False otherwise
    """
    return language_code.lower() in SUPPORTED_LANGUAGES


def get_language_name(language_code: str) -> str:
    """Get the full language name for a code.
    
    Args:
        language_code: ISO 639-1 language code
        
    Returns:
        Full language name or 'Unknown' if not supported
    """
    return SUPPORTED_LANGUAGES.get(language_code.lower(), "Unknown")
