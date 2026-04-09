"""Shared test fixtures."""

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def tmp_docs(tmp_path: Path) -> Path:
    """Create a temporary docs directory with sample markdown files."""
    (tmp_path / "hello.md").write_text("# Hello\nWorld", encoding="utf-8")
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "nested.md").write_text("# Nested\nContent", encoding="utf-8")
    return tmp_path


@pytest.fixture
def tmp_multi_docs(tmp_path: Path) -> dict[str, Path]:
    """Create multiple temporary doc directories."""
    notes = tmp_path / "notes_root"
    notes.mkdir()
    (notes / "todo.md").write_text("# Todo\nBuy milk", encoding="utf-8")
    (notes / "ideas.md").write_text("# Ideas\nBuild something", encoding="utf-8")
    notes_sub = notes / "archive"
    notes_sub.mkdir()
    (notes_sub / "old.md").write_text("# Old\nArchived note", encoding="utf-8")

    wiki = tmp_path / "wiki_root"
    wiki.mkdir()
    (wiki / "setup.md").write_text("# Setup\nInstall guide", encoding="utf-8")

    return {"notes": notes, "wiki": wiki}


@pytest.fixture
def client(tmp_docs: Path) -> TestClient:
    """Create a test client with a single root directory."""
    os.environ["CAPYDOCS_ROOT_DIRS"] = json.dumps({"": str(tmp_docs)})
    from capydocs.server import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture
def multi_client(tmp_multi_docs: dict[str, Path]) -> TestClient:
    """Create a test client with multiple root directories."""
    os.environ["CAPYDOCS_ROOT_DIRS"] = json.dumps(
        {name: str(path) for name, path in tmp_multi_docs.items()}
    )
    from capydocs.server import create_app

    app = create_app()
    return TestClient(app)
