"""MCP server for capydocs — exposes document management tools over Streamable HTTP."""

from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from capydocs.services.filesystem import (
    create_file,
    delete_file,
    get_tree,
    move_file,
    read_file,
    write_file,
)
from capydocs.services.search import search_files

mcp = FastMCP("capydocs")

# Will be set when the MCP server is mounted
_root_dir: Path = Path(".")


def set_root_dir(root_dir: Path) -> None:
    global _root_dir
    _root_dir = root_dir


@mcp.tool()
def list_docs() -> list[dict[str, Any]]:
    """List all markdown files as a tree structure.

    Returns a recursive tree of .md files under the configured root directory.
    Each entry has: name, path (relative), type ("file" or "directory"), and children (for directories).
    """
    return get_tree(_root_dir)


@mcp.tool()
def read_doc(path: str) -> str:
    """Read a markdown file and return its content.

    Args:
        path: Relative path to the markdown file (e.g. "guides/setup.md")
    """
    return read_file(_root_dir, path)


@mcp.tool()
def write_doc(path: str, content: str) -> str:
    """Create or update a markdown file.

    If the file exists, it will be overwritten. If it doesn't exist, it will be created.
    Parent directories are created automatically.

    Args:
        path: Relative path to the markdown file (e.g. "notes/meeting.md")
        content: The markdown content to write
    """
    try:
        write_file(_root_dir, path, content)
    except Exception:
        create_file(_root_dir, path, content)
    return f"Written: {path}"


@mcp.tool()
def delete_doc(path: str) -> str:
    """Delete a markdown file.

    Args:
        path: Relative path to the markdown file to delete
    """
    delete_file(_root_dir, path)
    return f"Deleted: {path}"


@mcp.tool()
def move_doc(path: str, destination: str) -> str:
    """Move or rename a markdown file.

    Args:
        path: Current relative path of the file (e.g. "notes/old-name.md")
        destination: New relative path for the file (e.g. "notes/new-name.md")
    """
    new_path = move_file(_root_dir, path, destination)
    return f"Moved: {path} -> {new_path}"


@mcp.tool()
def search_docs(query: str) -> list[dict[str, Any]]:
    """Search markdown files by filename and content.

    Returns matching files with context snippets showing where the match was found.

    Args:
        query: Search term to look for in filenames and file content
    """
    return search_files(_root_dir, query)
