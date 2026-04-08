"""Tests for search service and API."""

from pathlib import Path

from capydocs.services.search import search_files


def test_search_by_filename(tmp_docs: Path) -> None:
    results = search_files(tmp_docs, "hello")
    assert len(results) == 1
    assert results[0]["name"] == "hello.md"
    assert results[0]["name_match"] is True


def test_search_by_content(tmp_docs: Path) -> None:
    results = search_files(tmp_docs, "Nested")
    assert len(results) == 1
    assert results[0]["path"] == "subdir/nested.md"
    assert results[0]["content_match"] is True
    assert "Nested" in results[0]["context"]


def test_search_empty_query(tmp_docs: Path) -> None:
    results = search_files(tmp_docs, "")
    assert results == []


def test_search_no_match(tmp_docs: Path) -> None:
    results = search_files(tmp_docs, "nonexistent_term_xyz")
    assert results == []


def test_search_api(client) -> None:
    resp = client.get("/api/search?q=Hello")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert any(r["name"] == "hello.md" for r in results)
