"""Search service for markdown files."""

from pathlib import Path
from typing import Any


def search_files(root_dir: Path, query: str, max_results: int = 50) -> list[dict[str, Any]]:
    """Search markdown files by filename and content."""
    if not query.strip():
        return []

    query_lower = query.lower()
    results: list[dict[str, Any]] = []

    if not root_dir.is_dir():
        return results

    for md_file in sorted(root_dir.rglob("*.md")):
        if md_file.name.startswith("."):
            continue
        # Skip hidden directories
        if any(part.startswith(".") for part in md_file.relative_to(root_dir).parts):
            continue

        rel_path = str(md_file.relative_to(root_dir))
        name_match = query_lower in md_file.name.lower()

        try:
            content = md_file.read_text(encoding="utf-8")
        except (PermissionError, UnicodeDecodeError):
            continue

        content_lower = content.lower()
        content_match = query_lower in content_lower

        if name_match or content_match:
            context = ""
            if content_match:
                idx = content_lower.index(query_lower)
                start = max(0, idx - 40)
                end = min(len(content), idx + len(query) + 40)
                context = content[start:end].replace("\n", " ").strip()
                if start > 0:
                    context = "..." + context
                if end < len(content):
                    context = context + "..."

            results.append({
                "path": rel_path,
                "name": md_file.name,
                "name_match": name_match,
                "content_match": content_match,
                "context": context,
            })

        if len(results) >= max_results:
            break

    # Sort: name matches first, then content matches
    results.sort(key=lambda r: (not r["name_match"], r["path"]))
    return results
