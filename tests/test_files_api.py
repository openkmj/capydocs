"""Tests for files API endpoints."""


def test_get_tree(client) -> None:
    resp = client.get("/api/tree")
    assert resp.status_code == 200
    tree = resp.json()
    names = {e["name"] for e in tree}
    assert "hello.md" in names


def test_read_file(client) -> None:
    resp = client.get("/api/files/hello.md")
    assert resp.status_code == 200
    assert "# Hello" in resp.json()["content"]


def test_write_file(client) -> None:
    resp = client.put("/api/files/hello.md", json={"content": "# Updated"})
    assert resp.status_code == 200
    resp2 = client.get("/api/files/hello.md")
    assert resp2.json()["content"] == "# Updated"


def test_create_file(client) -> None:
    resp = client.post("/api/files/new.md", json={"content": "# New"})
    assert resp.status_code == 201


def test_delete_file(client) -> None:
    resp = client.delete("/api/files/hello.md")
    assert resp.status_code == 200
    resp2 = client.get("/api/files/hello.md")
    assert resp2.status_code == 404


def test_rename_file(client) -> None:
    resp = client.patch("/api/files/hello.md", json={"destination": "renamed.md"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "moved"
    resp2 = client.get("/api/files/renamed.md")
    assert resp2.status_code == 200


def test_rename_file_not_found(client) -> None:
    resp = client.patch("/api/files/nonexistent.md", json={"destination": "dest.md"})
    assert resp.status_code == 404


def test_path_traversal_blocked(client) -> None:
    resp = client.get("/api/files/../../etc/passwd")
    assert resp.status_code in (403, 400, 404)
