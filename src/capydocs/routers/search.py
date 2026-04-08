"""Search API endpoint."""

from typing import Any

from fastapi import APIRouter, Request

from capydocs.services.search import search_files

router = APIRouter(tags=["search"])


@router.get("/search")
async def api_search(q: str, request: Request) -> list[dict[str, Any]]:
    """Search markdown files by filename and content."""
    return search_files(request.app.state.root_dir, q)
