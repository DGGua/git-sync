"""FastAPI application for git-sync web frontend."""

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from git_sync.config.loader import ConfigManager
from git_sync.web.api import (
    config_router,
    repositories_router,
    keys_router,
    sync_router,
)
from git_sync.web.api.config import set_config_manager


def get_frontend_dist_dir() -> Path:
    """Get the frontend dist directory path."""
    # Check for frontend dist in multiple locations
    possible_paths = [
        Path(__file__).parent.parent.parent / "frontend" / "dist",
        Path(__file__).parent / "static",
        Path.cwd() / "frontend" / "dist",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: Initialize config manager
    config_manager = ConfigManager()
    set_config_manager(config_manager)
    yield
    # Shutdown: cleanup if needed


def create_app(config_path: str = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        config_path: Optional path to configuration directory

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Git Sync",
        description="Web frontend for git-sync configuration management",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Set custom config path if provided
    if config_path:
        config_manager = ConfigManager(config_path)
        set_config_manager(config_manager)

    # Include API routers
    app.include_router(config_router)
    app.include_router(repositories_router)
    app.include_router(keys_router)
    app.include_router(sync_router)

    # Serve frontend static files if available
    frontend_dist = get_frontend_dist_dir()
    if frontend_dist:
        # Serve static assets
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        # Serve index.html for all non-API routes (SPA fallback)
        @app.get("/{path:path}")
        async def serve_spa(path: str):
            """Serve the SPA index.html for all non-API routes."""
            # Don't intercept API routes
            if path.startswith("api/"):
                return None

            # Try to serve static files first
            file_path = frontend_dist / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))

            # Fall back to index.html for SPA routing
            index_path = frontend_dist / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))

            return {"error": "Frontend not built. Run 'npm run build' in frontend/ directory."}

    # Health check endpoint
    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok"}

    return app


# Default app instance for uvicorn
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "git_sync.web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
