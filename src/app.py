"""FastAPI application bootstrap."""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config.env import get_settings
from .routes import translate
from .routes import translate_preview


# Create FastAPI app
app = FastAPI(
    title="Azure Translation Service",
    description="Real-time translation with glossary enforcement for domain-specific terminology",
    version="1.0.0"
)

# Setup templates
templates_dir = Path(__file__).parent / "ui" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Include API routes
app.include_router(translate.router)
app.include_router(translate_preview.router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Initialize standard translator
    translate.initialize_services()
    
    # Initialize preview translator with shared services
    translate_preview.initialize_preview_services(
        post_editor_instance=translate.post_editor,
        glossary_loader_instance=translate.glossary_loader,
        enforcer_instance=translate.terminology_enforcer
    )
    
    print("Application started successfully")
    print("Standard Translator: Available")
    print(f"Preview Translator: {'Available' if translate_preview.preview_translator else 'Not configured'}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main UI page.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTML response with translation UI
    """
    settings = get_settings()
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "target_language": settings.target_language,
            "post_editor_enabled": settings.enable_post_editor,
            "preview_available": translate_preview.preview_translator is not None
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "src.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
