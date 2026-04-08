"""Tests for filesystem service."""

from pathlib import Path

import pytest
from fastapi import HTTPException

from capydocs.services.filesystem import (
    create_file,
    delete_file,
    get_tree,
    move_file,
    read_file,
    write_file,
)


def test_get_tree(tmp_docs: Path) -> None:
    tree = get_tree(tmp_docs)
    names = {e["name"] for e in tree}
    assert "subdir" in names
    assert "hello.md" in names


def test_get_tree_nested(tmp_docs: Path) -> None:
    tree = get_tree(tmp_docs)
    subdir = next(e for e in tree if e["name"] == "subdir")
    assert subdir["type"] == "directory"
    assert any(c["name"] == "nested.md" for c in subdir["children"])


def test_read_file(tmp_docs: Path) -> None:
    content = read_file(tmp_docs, "hello.md")
    assert "# Hello" in content


def test_read_file_not_found(tmp_docs: Path) -> None:
    with pytest.raises(HTTPException) as exc_info:
        read_file(tmp_docs, "nonexistent.md")
    assert exc_info.value.status_code == 404


def test_write_file(tmp_docs: Path) -> None:
    write_file(tmp_docs, "hello.md", "# Updated")
    assert (tmp_docs / "hello.md").read_text() == "# Updated"


def test_create_file(tmp_docs: Path) -> None:
    create_file(tmp_docs, "new.md", "# New")
    assert (tmp_docs / "new.md").read_text() == "# New"


def test_create_file_auto_suffix(tmp_docs: Path) -> None:
    create_file(tmp_docs, "auto", "# Auto")
    assert (tmp_docs / "auto.md").exists()


def test_create_file_conflict(tmp_docs: Path) -> None:
    with pytest.raises(HTTPException) as exc_info:
        create_file(tmp_docs, "hello.md")
    assert exc_info.value.status_code == 409


def test_delete_file(tmp_docs: Path) -> None:
    delete_file(tmp_docs, "hello.md")
    assert not (tmp_docs / "hello.md").exists()


def test_move_file(tmp_docs: Path) -> None:
    new_path = move_file(tmp_docs, "hello.md", "renamed.md")
    assert new_path == "renamed.md"
    assert not (tmp_docs / "hello.md").exists()
    assert (tmp_docs / "renamed.md").read_text() == "# Hello\nWorld"


def test_move_file_to_subdir(tmp_docs: Path) -> None:
    new_path = move_file(tmp_docs, "hello.md", "newdir/hello.md")
    assert new_path == "newdir/hello.md"
    assert (tmp_docs / "newdir" / "hello.md").is_file()


def test_move_file_auto_suffix(tmp_docs: Path) -> None:
    new_path = move_file(tmp_docs, "hello.md", "renamed")
    assert new_path == "renamed.md"


def test_move_file_not_found(tmp_docs: Path) -> None:
    with pytest.raises(HTTPException) as exc_info:
        move_file(tmp_docs, "nonexistent.md", "dest.md")
    assert exc_info.value.status_code == 404


def test_move_file_conflict(tmp_docs: Path) -> None:
    create_file(tmp_docs, "other.md", "# Other")
    with pytest.raises(HTTPException) as exc_info:
        move_file(tmp_docs, "hello.md", "other.md")
    assert exc_info.value.status_code == 409


def test_path_traversal(tmp_docs: Path) -> None:
    with pytest.raises(HTTPException) as exc_info:
        read_file(tmp_docs, "../../etc/passwd")
    assert exc_info.value.status_code == 403
