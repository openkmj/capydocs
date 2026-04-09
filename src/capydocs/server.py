"""FastAPI application factory."""

import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Parse root dirs from env (set by CLI)
    raw = os.environ.get("CAPYDOCS_ROOT_DIRS", "")
    if raw:
        root_dirs = {name: Path(p).resolve() for name, p in json.loads(raw).items()}
    else:
        root_dirs = {"": Path(".").resolve()}

    # Set up MCP server
    from capydocs.mcp_server import mcp, set_root_dirs

    set_root_dirs(root_dirs)
    mcp_app = mcp.http_app(path="/", transport="streamable-http")

    # Use MCP app's lifespan so its session manager is properly initialized
    app = FastAPI(title="capydocs", version="0.3.0", lifespan=mcp_app.lifespan)
    app.state.root_dirs = root_dirs

    # Register routers
    from capydocs.routers.ai import router as ai_router
    from capydocs.routers.files import router as files_router
    from capydocs.routers.search import router as search_router

    app.include_router(files_router, prefix="/api")
    app.include_router(search_router, prefix="/api")
    app.include_router(ai_router, prefix="/api")

    # Mount MCP server at /mcp
    app.mount("/mcp", mcp_app)

    # Serve static frontend files (must be last — catches all routes)
    static_dir = Path(__file__).parent / "static"
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app
