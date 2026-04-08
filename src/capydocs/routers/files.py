"""File management API endpoints."""

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from capydocs.services.filesystem import (
    create_directory,
    create_file,
    delete_directory,
    delete_file,
    get_tree,
    move_file,
    read_file,
    write_file,
)

router = APIRouter(tags=["files"])


class FileContent(BaseModel):
    content: str = ""


class MoveRequest(BaseModel):
    destination: str


@router.get("/tree")
async def api_get_tree(request: Request) -> list[dict[str, Any]]:
    """Get the markdown file tree."""
    return get_tree(request.app.state.root_dir)


@router.get("/files/{path:path}")
async def api_read_file(path: str, request: Request) -> dict[str, str]:
    """Read a markdown file."""
    content = read_file(request.app.state.root_dir, path)
    return {"path": path, "content": content}


@router.put("/files/{path:path}")
async def api_write_file(path: str, body: FileContent, request: Request) -> dict[str, str]:
    """Update a markdown file."""
    formatted = write_file(request.app.state.root_dir, path, body.content)
    return {"path": path, "status": "saved", "content": formatted}


@router.post("/files/{path:path}", status_code=201)
async def api_create_file(path: str, body: FileContent, request: Request) -> dict[str, str]:
    """Create a new markdown file."""
    create_file(request.app.state.root_dir, path, body.content)
    return {"path": path, "status": "created"}


@router.patch("/files/{path:path}")
async def api_move_file(path: str, body: MoveRequest, request: Request) -> dict[str, str]:
    """Move or rename a markdown file."""
    new_path = move_file(request.app.state.root_dir, path, body.destination)
    return {"path": new_path, "status": "moved"}


@router.post("/dirs/{path:path}", status_code=201)
async def api_create_directory(path: str, request: Request) -> dict[str, str]:
    """Create a new directory."""
    create_directory(request.app.state.root_dir, path)
    return {"path": path, "status": "created"}


@router.delete("/dirs/{path:path}")
async def api_delete_directory(path: str, request: Request) -> dict[str, str]:
    """Delete an empty directory."""
    delete_directory(request.app.state.root_dir, path)
    return {"path": path, "status": "deleted"}


@router.delete("/files/{path:path}")
async def api_delete_file(path: str, request: Request) -> dict[str, str]:
    """Delete a markdown file."""
    delete_file(request.app.state.root_dir, path)
    return {"path": path, "status": "deleted"}
