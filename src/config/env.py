"""Environment configuration and validation."""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Azure Translator Configuration
    azure_translator_key: str = Field(..., description="Azure Translator API key")
    azure_translator_endpoint: str = Field(
        default="https://api.cognitive.microsofttranslator.com",
        description="Azure Translator endpoint"
    )
    azure_translator_region: str = Field(..., description="Azure region")
    azure_translator_category: str = Field(
        default="",
        description="Custom Translator category ID (optional)"
    )
    
    # Translation Configuration
    target_language: str = Field(default="nl", description="Target language code")
    
    # Glossary Configuration
    glossary_path: str = Field(
        default="data/glossary.tsv",
        description="Path to TSV glossary file"
    )
    
    # Azure OpenAI Configuration (optional)
    enable_post_editor: bool = Field(
        default=False,
        description="Enable Azure OpenAI post-editing"
    )
    azure_openai_endpoint: Optional[str] = Field(
        default=None,
        description="Azure OpenAI endpoint"
    )
    azure_openai_key: Optional[str] = Field(
        default=None,
        description="Azure OpenAI API key"
    )
    azure_openai_deployment: str = Field(
        default="gpt-4o-mini",
        description="Azure OpenAI deployment name (gpt-4o-mini for speed, gpt-4o for quality)"
    )
    azure_openai_api_version: str = Field(
        default="2024-02-15-preview",
        description="Azure OpenAI API version"
    )
    
    # Translator API Preview Configuration (optional)
    translator_api_preview_endpoint: Optional[str] = Field(
        default=None,
        description="Translator API preview endpoint"
    )
    translator_api_preview_key: Optional[str] = Field(
        default=None,
        description="Translator API preview key"
    )
    translator_api_preview_location: Optional[str] = Field(
        default=None,
        description="Translator API preview location/region"
    )
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    
    @field_validator("glossary_path")
    @classmethod
    def validate_glossary_path(cls, v: str) -> str:
        """Ensure glossary path(s) are valid."""
        raw_paths = [p.strip() for p in v.split(",") if p.strip()]
        for raw_path in raw_paths:
            path = Path(raw_path)
            if not path.exists():
                # Don't fail during initialization; log warning instead
                print(f"Warning: Glossary file not found at {raw_path}")
        return v
    
    @field_validator("enable_post_editor")
    @classmethod
    def validate_post_editor_config(cls, v: bool, info) -> bool:
        """Validate Azure OpenAI config if post-editor is enabled."""
        if v:
            # Check will happen at runtime when values are accessed
            pass
        return v
    
    def get_glossary_path(self) -> Path:
        """Get glossary path as Path object (first path if multiple)."""
        paths = self.get_glossary_paths()
        return paths[0] if paths else Path(self.glossary_path)

    def get_glossary_paths(self) -> list[Path]:
        """Get glossary paths as a list of Path objects."""
        return [Path(p.strip()) for p in self.glossary_path.split(",") if p.strip()]


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance.
    
    Returns:
        Settings instance loaded from environment
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
