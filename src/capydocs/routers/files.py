"""File management API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from capydocs.services.filesystem import (
    create_directory,
    create_file,
    delete_directory,
    delete_file,
    get_multi_tree,
    move_file,
    read_file,
    resolve_root,
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
    return get_multi_tree(request.app.state.root_dirs)


@router.get("/files/{path:path}")
async def api_read_file(path: str, request: Request) -> dict[str, str]:
    """Read a markdown file."""
    root_dir, rel_path = resolve_root(request.app.state.root_dirs, path)
    content = read_file(root_dir, rel_path)
    return {"path": path, "content": content}


@router.put("/files/{path:path}")
async def api_write_file(path: str, body: FileContent, request: Request) -> dict[str, str]:
    """Update a markdown file."""
    root_dir, rel_path = resolve_root(request.app.state.root_dirs, path)
    write_file(root_dir, rel_path, body.content)
    return {"path": path, "status": "saved"}


@router.post("/files/{path:path}", status_code=201)
async def api_create_file(path: str, body: FileContent, request: Request) -> dict[str, str]:
    """Create a new markdown file."""
    root_dir, rel_path = resolve_root(request.app.state.root_dirs, path)
    create_file(root_dir, rel_path, body.content)
    return {"path": path, "status": "created"}


@router.patch("/files/{path:path}")
async def api_move_file(path: str, body: MoveRequest, request: Request) -> dict[str, str]:
    """Move or rename a markdown file."""
    root_dir, rel_path = resolve_root(request.app.state.root_dirs, path)
    # Resolve destination within the same root
    dest_root, dest_rel = resolve_root(request.app.state.root_dirs, body.destination)
    if dest_root != root_dir:
        # For cross-root moves, use the destination root
        pass
    new_rel = move_file(root_dir, rel_path, dest_rel)
    # Reconstruct full path with root prefix if multi-root
    root_dirs = request.app.state.root_dirs
    if "" not in root_dirs:
        root_name = path.split("/", 1)[0]
        new_path = f"{root_name}/{new_rel}"
    else:
        new_path = new_rel
    return {"path": new_path, "status": "moved"}


@router.post("/dirs/{path:path}", status_code=201)
async def api_create_directory(path: str, request: Request) -> dict[str, str]:
    """Create a new directory."""
    root_dir, rel_path = resolve_root(request.app.state.root_dirs, path)
    create_directory(root_dir, rel_path)
    return {"path": path, "status": "created"}


@router.delete("/dirs/{path:path}")
async def api_delete_directory(path: str, request: Request) -> dict[str, str]:
    """Delete an empty directory."""
    root_dir, rel_path = resolve_root(request.app.state.root_dirs, path)
    if not rel_path:
        raise HTTPException(status_code=403, detail="Cannot delete a root directory")
    delete_directory(root_dir, rel_path)
    return {"path": path, "status": "deleted"}


@router.delete("/files/{path:path}")
async def api_delete_file(path: str, request: Request) -> dict[str, str]:
    """Delete a markdown file."""
    root_dir, rel_path = resolve_root(request.app.state.root_dirs, path)
    delete_file(root_dir, rel_path)
    return {"path": path, "status": "deleted"}
