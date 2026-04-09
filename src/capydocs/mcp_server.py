"""MCP server for capydocs — exposes document management tools over Streamable HTTP."""

from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from capydocs.services.filesystem import (
    create_file,
    delete_file,
    get_multi_tree,
    move_file,
    read_file,
    resolve_root,
    write_file,
)
from capydocs.services.search import search_files_multi

mcp = FastMCP("capydocs")

# Will be set when the MCP server is mounted
_root_dirs: dict[str, Path] = {"": Path(".")}


def set_root_dirs(root_dirs: dict[str, Path]) -> None:
    global _root_dirs
    _root_dirs = root_dirs


@mcp.tool()
def list_docs(path: str | None = None) -> list[dict[str, Any]]:
    """List markdown files as a tree structure.

    Returns a recursive tree of .md files under the configured root directories.
    Each entry has: name, path (relative), type ("file" or "directory"), and children (for directories).

    Args:
        path: Optional sub-path to list only a specific folder (e.g. "notes/archive")
    """
    return get_multi_tree(_root_dirs, sub_path=path)


@mcp.tool()
def read_doc(path: str) -> str:
    """Read a markdown file and return its content.

    Args:
        path: Relative path to the markdown file (e.g. "guides/setup.md")
    """
    root_dir, rel_path = resolve_root(_root_dirs, path)
    return read_file(root_dir, rel_path)


@mcp.tool()
def write_doc(path: str, content: str) -> str:
    """Create or update a markdown file.

    If the file exists, it will be overwritten. If it doesn't exist, it will be created.
    Parent directories are created automatically.

    Args:
        path: Relative path to the markdown file (e.g. "notes/meeting.md")
        content: The markdown content to write
    """
    root_dir, rel_path = resolve_root(_root_dirs, path)
    try:
        write_file(root_dir, rel_path, content)
    except Exception:
        create_file(root_dir, rel_path, content)
    return f"Written: {path}"


@mcp.tool()
def delete_doc(path: str) -> str:
    """Delete a markdown file.

    Args:
        path: Relative path to the markdown file to delete
    """
    root_dir, rel_path = resolve_root(_root_dirs, path)
    delete_file(root_dir, rel_path)
    return f"Deleted: {path}"


@mcp.tool()
def move_doc(path: str, destination: str) -> str:
    """Move or rename a markdown file.

    Args:
        path: Current relative path of the file (e.g. "notes/old-name.md")
        destination: New relative path for the file (e.g. "notes/new-name.md")
    """
    root_dir, rel_path = resolve_root(_root_dirs, path)
    _, dest_rel = resolve_root(_root_dirs, destination)
    new_path = move_file(root_dir, rel_path, dest_rel)
    return f"Moved: {path} -> {new_path}"


@mcp.tool()
def search_docs(query: str) -> list[dict[str, Any]]:
    """Search markdown files by filename and content.

    Returns matching files with context snippets showing where the match was found.

    Args:
        query: Search term to look for in filenames and file content
    """
    return search_files_multi(_root_dirs, query)
