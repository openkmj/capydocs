"""Tests for AI refinement API."""

from unittest.mock import AsyncMock, patch


def test_refine_empty_text(client) -> None:
    resp = client.post("/api/ai/refine", json={"text": "", "instruction": "compact"})
    assert resp.status_code == 400


def test_refine_no_api_key(client) -> None:
    resp = client.post("/api/ai/refine", json={"text": "hello world", "preset": "compact"})
    assert resp.status_code == 422


def test_get_presets(client) -> None:
    resp = client.get("/api/ai/presets")
    assert resp.status_code == 200
    presets = resp.json()
    assert "compact" in presets
    assert "fix" in presets
    assert "translate_en" in presets
    assert "translate_ko" in presets


@patch("capydocs.routers.ai.refine_text", new_callable=AsyncMock)
def test_refine_with_mock(mock_refine, client) -> None:
    mock_refine.return_value = {
        "refined": "Hello, world!",
        "model": "gpt-5-mini",
    }

    resp = client.post(
        "/api/ai/refine",
        json={"text": "hello world", "preset": "fix"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["refined"] == "Hello, world!"
    assert data["model"] == "gpt-5-mini"
