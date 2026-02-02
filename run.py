#!/usr/bin/env python3
"""Run the Azure Translation Service application."""

import uvicorn
from src.config.env import get_settings

if __name__ == "__main__":
    settings = get_settings()
    
    print(f"Starting Azure Translation Service...")
    print(f"Server: http://{settings.host}:{settings.port}")
    print(f"Target Language: {settings.target_language}")
    print(f"Glossary: {settings.glossary_path}")
    print(f"Post-Editor: {'Enabled' if settings.enable_post_editor else 'Disabled'}")
    print()
    
    uvicorn.run(
        "src.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
