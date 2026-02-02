"""FastAPI application bootstrap."""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config.env import get_settings
from .routes import translate


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


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    translate.initialize_services()
    print("Application started successfully")


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
            "post_editor_enabled": settings.enable_post_editor
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
