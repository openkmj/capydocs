"""Search API endpoint."""

from typing import Any

from fastapi import APIRouter, Request

from capydocs.services.search import search_files_multi

router = APIRouter(tags=["search"])


@router.get("/search")
async def api_search(
    q: str, request: Request, path: str | None = None
) -> list[dict[str, Any]]:
    """Search markdown files by filename and content.

    Optionally restrict search to a sub-path (e.g. ?path=notes/archive).
    """
    return search_files_multi(request.app.state.root_dirs, q, path=path)
