"""Shared test fixtures."""

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
def client(tmp_docs: Path) -> TestClient:
    """Create a test client with a temporary root directory."""
    os.environ["DOCPYBARA_ROOT_DIR"] = str(tmp_docs)
    from capydocs.server import create_app

    app = create_app()
    return TestClient(app)
