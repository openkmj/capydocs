"""Tests for multi-root directory support."""

from pathlib import Path

import pytest
from fastapi import HTTPException

from capydocs.services.filesystem import (
    get_multi_tree,
    resolve_root,
)
from capydocs.services.search import search_files_multi

# --- resolve_root ---


class TestResolveRoot:
    def test_single_root_passthrough(self, tmp_docs: Path) -> None:
        """Single root (empty key) passes path through unchanged."""
        root_dirs = {"": tmp_docs}
        root, rel = resolve_root(root_dirs, "hello.md")
        assert root == tmp_docs
        assert rel == "hello.md"

    def test_single_root_nested_path(self, tmp_docs: Path) -> None:
        root_dirs = {"": tmp_docs}
        root, rel = resolve_root(root_dirs, "subdir/nested.md")
        assert root == tmp_docs
        assert rel == "subdir/nested.md"

    def test_multi_root_resolves_first_segment(self, tmp_multi_docs: dict[str, Path]) -> None:
        root_dirs = tmp_multi_docs
        root, rel = resolve_root(root_dirs, "notes/todo.md")
        assert root == tmp_multi_docs["notes"]
        assert rel == "todo.md"

    def test_multi_root_resolves_nested(self, tmp_multi_docs: dict[str, Path]) -> None:
        root_dirs = tmp_multi_docs
        root, rel = resolve_root(root_dirs, "notes/archive/old.md")
        assert root == tmp_multi_docs["notes"]
        assert rel == "archive/old.md"

    def test_multi_root_different_roots(self, tmp_multi_docs: dict[str, Path]) -> None:
        root_dirs = tmp_multi_docs
        root, rel = resolve_root(root_dirs, "wiki/setup.md")
        assert root == tmp_multi_docs["wiki"]
        assert rel == "setup.md"

    def test_multi_root_unknown_root_raises(self, tmp_multi_docs: dict[str, Path]) -> None:
        root_dirs = tmp_multi_docs
        with pytest.raises(HTTPException) as exc_info:
            resolve_root(root_dirs, "unknown/file.md")
        assert exc_info.value.status_code == 404

    def test_multi_root_bare_name_empty_remaining(
        self, tmp_multi_docs: dict[str, Path]
    ) -> None:
        """Path with just the root name gives empty remaining."""
        root_dirs = tmp_multi_docs
        root, rel = resolve_root(root_dirs, "notes")
        assert root == tmp_multi_docs["notes"]
        assert rel == ""


# --- get_multi_tree ---


class TestGetMultiTree:
    def test_single_root_returns_flat_tree(self, tmp_docs: Path) -> None:
        root_dirs = {"": tmp_docs}
        tree = get_multi_tree(root_dirs)
        names = {e["name"] for e in tree}
        assert "hello.md" in names
        assert "subdir" in names

    def test_multi_root_returns_root_folders(self, tmp_multi_docs: dict[str, Path]) -> None:
        tree = get_multi_tree(tmp_multi_docs)
        root_names = {e["name"] for e in tree}
        assert root_names == {"notes", "wiki"}

    def test_multi_root_all_entries_are_directories(
        self, tmp_multi_docs: dict[str, Path]
    ) -> None:
        tree = get_multi_tree(tmp_multi_docs)
        assert all(e["type"] == "directory" for e in tree)

    def test_multi_root_children_have_prefixed_paths(
        self, tmp_multi_docs: dict[str, Path]
    ) -> None:
        tree = get_multi_tree(tmp_multi_docs)
        notes = next(e for e in tree if e["name"] == "notes")
        child_paths = {c["path"] for c in notes["children"]}
        assert "notes/todo.md" in child_paths
        assert "notes/ideas.md" in child_paths

    def test_multi_root_nested_children_prefixed(
        self, tmp_multi_docs: dict[str, Path]
    ) -> None:
        tree = get_multi_tree(tmp_multi_docs)
        notes = next(e for e in tree if e["name"] == "notes")
        archive = next(c for c in notes["children"] if c["name"] == "archive")
        assert archive["path"] == "notes/archive"
        old = next(c for c in archive["children"] if c["name"] == "old.md")
        assert old["path"] == "notes/archive/old.md"

    def test_multi_root_wiki_children(self, tmp_multi_docs: dict[str, Path]) -> None:
        tree = get_multi_tree(tmp_multi_docs)
        wiki = next(e for e in tree if e["name"] == "wiki")
        child_paths = {c["path"] for c in wiki["children"]}
        assert "wiki/setup.md" in child_paths

    def test_multi_root_sorted_alphabetically(self, tmp_multi_docs: dict[str, Path]) -> None:
        tree = get_multi_tree(tmp_multi_docs)
        names = [e["name"] for e in tree]
        assert names == sorted(names)


# --- get_multi_tree sub-path filtering ---


class TestGetMultiTreeSubPath:
    def test_single_root_sub_path(self, tmp_docs: Path) -> None:
        root_dirs = {"": tmp_docs}
        tree = get_multi_tree(root_dirs, sub_path="subdir")
        names = {e["name"] for e in tree}
        assert "nested.md" in names

    def test_single_root_sub_path_has_correct_paths(self, tmp_docs: Path) -> None:
        root_dirs = {"": tmp_docs}
        tree = get_multi_tree(root_dirs, sub_path="subdir")
        paths = {e["path"] for e in tree}
        assert "subdir/nested.md" in paths

    def test_multi_root_sub_path(self, tmp_multi_docs: dict[str, Path]) -> None:
        tree = get_multi_tree(tmp_multi_docs, sub_path="notes/archive")
        names = {e["name"] for e in tree}
        assert "old.md" in names

    def test_multi_root_sub_path_has_prefixed_paths(
        self, tmp_multi_docs: dict[str, Path]
    ) -> None:
        tree = get_multi_tree(tmp_multi_docs, sub_path="notes/archive")
        paths = {e["path"] for e in tree}
        assert "notes/archive/old.md" in paths

    def test_multi_root_sub_path_root_level(self, tmp_multi_docs: dict[str, Path]) -> None:
        """Listing a root name returns its direct contents."""
        tree = get_multi_tree(tmp_multi_docs, sub_path="wiki")
        names = {e["name"] for e in tree}
        assert "setup.md" in names

    def test_sub_path_nonexistent_raises(self, tmp_multi_docs: dict[str, Path]) -> None:
        with pytest.raises(HTTPException) as exc_info:
            get_multi_tree(tmp_multi_docs, sub_path="notes/nonexistent")
        assert exc_info.value.status_code == 404

    def test_no_sub_path_returns_full_tree(self, tmp_multi_docs: dict[str, Path]) -> None:
        tree = get_multi_tree(tmp_multi_docs, sub_path=None)
        root_names = {e["name"] for e in tree}
        assert root_names == {"notes", "wiki"}


class TestSubPathAPI:
    def test_tree_with_sub_path(self, client) -> None:
        resp = client.get("/api/tree?path=subdir")
        assert resp.status_code == 200
        names = {e["name"] for e in resp.json()}
        assert "nested.md" in names

    def test_tree_without_sub_path(self, client) -> None:
        resp = client.get("/api/tree")
        assert resp.status_code == 200
        names = {e["name"] for e in resp.json()}
        assert "hello.md" in names

    def test_multi_tree_with_sub_path(self, multi_client) -> None:
        resp = multi_client.get("/api/tree?path=notes/archive")
        assert resp.status_code == 200
        names = {e["name"] for e in resp.json()}
        assert "old.md" in names

    def test_multi_tree_sub_path_not_found(self, multi_client) -> None:
        resp = multi_client.get("/api/tree?path=notes/nonexistent")
        assert resp.status_code == 404


# --- search_files_multi ---


class TestSearchFilesMulti:
    def test_single_root_search(self, tmp_docs: Path) -> None:
        root_dirs = {"": tmp_docs}
        results = search_files_multi(root_dirs, "Hello")
        assert len(results) == 1
        assert results[0]["path"] == "hello.md"

    def test_multi_root_search_finds_across_roots(
        self, tmp_multi_docs: dict[str, Path]
    ) -> None:
        results = search_files_multi(tmp_multi_docs, "Setup")
        assert len(results) >= 1
        assert any(r["path"] == "wiki/setup.md" for r in results)

    def test_multi_root_search_prefixes_paths(
        self, tmp_multi_docs: dict[str, Path]
    ) -> None:
        results = search_files_multi(tmp_multi_docs, "todo")
        assert len(results) >= 1
        assert results[0]["path"].startswith("notes/")

    def test_multi_root_search_across_all(self, tmp_multi_docs: dict[str, Path]) -> None:
        """A broad query should find results from multiple roots."""
        results = search_files_multi(tmp_multi_docs, "#")
        roots_found = {r["path"].split("/")[0] for r in results}
        assert "notes" in roots_found
        assert "wiki" in roots_found

    def test_multi_root_search_no_match(self, tmp_multi_docs: dict[str, Path]) -> None:
        results = search_files_multi(tmp_multi_docs, "nonexistent_xyz")
        assert results == []

    def test_multi_root_search_max_results(self, tmp_multi_docs: dict[str, Path]) -> None:
        results = search_files_multi(tmp_multi_docs, "#", max_results=2)
        assert len(results) <= 2


# --- Multi-root API tests ---


class TestMultiRootAPI:
    def test_tree_shows_roots(self, multi_client) -> None:
        resp = multi_client.get("/api/tree")
        assert resp.status_code == 200
        tree = resp.json()
        root_names = {e["name"] for e in tree}
        assert root_names == {"notes", "wiki"}

    def test_read_file_from_root(self, multi_client) -> None:
        resp = multi_client.get("/api/files/notes/todo.md")
        assert resp.status_code == 200
        assert "# Todo" in resp.json()["content"]

    def test_read_file_from_other_root(self, multi_client) -> None:
        resp = multi_client.get("/api/files/wiki/setup.md")
        assert resp.status_code == 200
        assert "# Setup" in resp.json()["content"]

    def test_read_nested_file(self, multi_client) -> None:
        resp = multi_client.get("/api/files/notes/archive/old.md")
        assert resp.status_code == 200
        assert "# Old" in resp.json()["content"]

    def test_read_unknown_root(self, multi_client) -> None:
        resp = multi_client.get("/api/files/unknown/file.md")
        assert resp.status_code == 404

    def test_write_file(self, multi_client) -> None:
        resp = multi_client.put("/api/files/notes/todo.md", json={"content": "# Updated"})
        assert resp.status_code == 200
        resp2 = multi_client.get("/api/files/notes/todo.md")
        assert resp2.json()["content"] == "# Updated"

    def test_create_file(self, multi_client) -> None:
        resp = multi_client.post("/api/files/wiki/new.md", json={"content": "# New"})
        assert resp.status_code == 201
        resp2 = multi_client.get("/api/files/wiki/new.md")
        assert resp2.status_code == 200

    def test_delete_file(self, multi_client) -> None:
        resp = multi_client.delete("/api/files/notes/ideas.md")
        assert resp.status_code == 200
        resp2 = multi_client.get("/api/files/notes/ideas.md")
        assert resp2.status_code == 404

    def test_rename_file(self, multi_client) -> None:
        resp = multi_client.patch(
            "/api/files/notes/todo.md", json={"destination": "notes/done.md"}
        )
        assert resp.status_code == 200
        assert resp.json()["path"] == "notes/done.md"
        resp2 = multi_client.get("/api/files/notes/done.md")
        assert resp2.status_code == 200

    def test_create_directory(self, multi_client) -> None:
        resp = multi_client.post("/api/dirs/notes/newdir")
        assert resp.status_code == 201

    def test_delete_directory(self, multi_client) -> None:
        multi_client.post("/api/dirs/wiki/tmpdir")
        resp = multi_client.delete("/api/dirs/wiki/tmpdir")
        assert resp.status_code == 200

    def test_search_across_roots(self, multi_client) -> None:
        resp = multi_client.get("/api/search?q=Setup")
        assert resp.status_code == 200
        results = resp.json()
        assert any(r["path"] == "wiki/setup.md" for r in results)

    def test_path_traversal_blocked(self, multi_client) -> None:
        resp = multi_client.get("/api/files/notes/../../etc/passwd")
        assert resp.status_code in (403, 400, 404)
