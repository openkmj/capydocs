"""Filesystem service for markdown file operations."""

from pathlib import Path
from typing import Any

from fastapi import HTTPException


def resolve_root(root_dirs: dict[str, Path], relative_path: str) -> tuple[Path, str]:
    """Resolve which root directory a path belongs to.

    For single root (key ""), the path is used as-is.
    For multi-root, the first path segment is the root name.
    """
    if "" in root_dirs:
        return root_dirs[""], relative_path

    parts = relative_path.split("/", 1)
    root_name = parts[0]
    remaining = parts[1] if len(parts) > 1 else ""

    if root_name not in root_dirs:
        raise HTTPException(status_code=404, detail=f"Unknown root: {root_name}")

    return root_dirs[root_name], remaining


def _validate_path(root_dir: Path, relative_path: str) -> Path:
    """Validate and resolve a path, preventing path traversal attacks."""
    resolved = (root_dir / relative_path).resolve()
    if not str(resolved).startswith(str(root_dir)):
        raise HTTPException(status_code=403, detail="Access denied: path traversal detected")
    return resolved


def get_tree(root_dir: Path) -> list[dict[str, Any]]:
    """Get a recursive tree of markdown files under a single root_dir."""
    if not root_dir.is_dir():
        return []

    def _build_tree(directory: Path) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        try:
            items = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return entries

        for item in items:
            if item.name.startswith("."):
                continue
            if item.is_dir():
                children = _build_tree(item)
                entries.append({
                    "name": item.name,
                    "path": str(item.relative_to(root_dir)),
                    "type": "directory",
                    "children": children,
                })
            elif item.suffix.lower() == ".md":
                entries.append({
                    "name": item.name,
                    "path": str(item.relative_to(root_dir)),
                    "type": "file",
                })
        return entries

    return _build_tree(root_dir)


def get_multi_tree(root_dirs: dict[str, Path]) -> list[dict[str, Any]]:
    """Get a merged tree from multiple root directories."""
    if "" in root_dirs:
        return get_tree(root_dirs[""])

    result: list[dict[str, Any]] = []
    for name, path in sorted(root_dirs.items()):
        children = get_tree(path)
        _prefix_paths(children, name)
        result.append({
            "name": name,
            "path": name,
            "type": "directory",
            "children": children,
        })
    return result


def _prefix_paths(items: list[dict[str, Any]], prefix: str) -> None:
    """Recursively prefix all paths in tree items."""
    for item in items:
        item["path"] = f"{prefix}/{item['path']}"
        if "children" in item:
            _prefix_paths(item["children"], prefix)


def read_file(root_dir: Path, relative_path: str) -> str:
    """Read a markdown file and return its content."""
    file_path = _validate_path(root_dir, relative_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {relative_path}")
    return file_path.read_text(encoding="utf-8")


def write_file(root_dir: Path, relative_path: str, content: str) -> None:
    """Write content to a markdown file."""
    file_path = _validate_path(root_dir, relative_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {relative_path}")
    file_path.write_text(content, encoding="utf-8")


def create_file(root_dir: Path, relative_path: str, content: str = "") -> None:
    """Create a new markdown file."""
    if not relative_path.endswith(".md"):
        relative_path += ".md"
    file_path = _validate_path(root_dir, relative_path)
    if file_path.exists():
        raise HTTPException(status_code=409, detail=f"File already exists: {relative_path}")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def move_file(root_dir: Path, src_path: str, dest_path: str) -> str:
    """Move or rename a markdown file. Returns the final relative path."""
    if not dest_path.endswith(".md"):
        dest_path += ".md"
    src = _validate_path(root_dir, src_path)
    dest = _validate_path(root_dir, dest_path)
    if not src.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {src_path}")
    if dest.exists():
        raise HTTPException(status_code=409, detail=f"Destination already exists: {dest_path}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dest)
    return str(dest.relative_to(root_dir))


def create_directory(root_dir: Path, relative_path: str) -> None:
    """Create a new directory."""
    dir_path = _validate_path(root_dir, relative_path)
    if dir_path.exists():
        raise HTTPException(status_code=409, detail=f"Already exists: {relative_path}")
    dir_path.mkdir(parents=True)


def delete_directory(root_dir: Path, relative_path: str) -> None:
    """Delete an empty directory."""
    dir_path = _validate_path(root_dir, relative_path)
    if not dir_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Directory not found: {relative_path}")
    if dir_path == root_dir.resolve():
        raise HTTPException(status_code=403, detail="Cannot delete root directory")
    try:
        dir_path.rmdir()
    except OSError as e:
        raise HTTPException(
            status_code=409, detail="Directory is not empty"
        ) from e


def delete_file(root_dir: Path, relative_path: str) -> None:
    """Delete a markdown file."""
    file_path = _validate_path(root_dir, relative_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {relative_path}")
    file_path.unlink()
