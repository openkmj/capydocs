# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is capydocs

A pip-installable, web-based markdown document manager. Point it at a directory and manage `.md` files through a dark-themed SPA with AI text refinement. Also exposes an MCP server for AI agent integration.

## Commands

```bash
make install    # uv pip install -e ".[dev,ai]"
make test       # uv run pytest tests/ -v
make lint       # uv run ruff check src/ tests/
make format     # uv run ruff check --fix src/ tests/
make dev        # Start server with auto-reload on port 8000
make build      # Build package to dist/
```

Run a single test:
```bash
uv run pytest tests/test_files_api.py -v
uv run pytest tests/test_files_api.py::test_name -v
```

## Architecture

```
CLI (click) → sets DOCPYBARA_ROOT_DIR env var → uvicorn → create_app() factory
```

**App factory** ([server.py](src/capydocs/server.py)): `create_app()` reads `DOCPYBARA_ROOT_DIR`, stores it in `app.state.root_dir`, registers routers under `/api`, mounts MCP at `/mcp`, and serves static frontend at `/`.

**Routers → Services pattern**: Routers handle HTTP/validation, services contain business logic. All file I/O goes through `services/filesystem.py` which enforces path traversal protection via `_validate_path()`. Routers access root_dir via `request.app.state.root_dir`.

**MCP server** ([mcp_server.py](src/capydocs/mcp_server.py)): Uses FastMCP, mounted as a sub-application. Has its own `_root_dir` module global set via `set_root_dir()` during app creation. Exposes the same filesystem/search services as MCP tools.

**Frontend**: Vanilla JS SPA in `src/capydocs/static/`. CodeMirror 6 is pre-bundled as `cm-bundle.js` — no npm/build step needed.

**AI service**: OpenAI `gpt-5-mini` integration in `services/ai.py`. Import is deferred inside the function to keep it optional. Requires `OPENAI_API_KEY` env var.

## Testing

Tests use `pytest` + `httpx` via FastAPI's `TestClient`. The `conftest.py` provides:
- `tmp_docs` fixture: creates a temp directory with sample `.md` files
- `client` fixture: sets `DOCPYBARA_ROOT_DIR` to `tmp_docs` and returns a `TestClient`

No database — all tests use the filesystem via `tmp_path`.

## Code Style

- **Linter**: ruff (rules: E, F, I, UP, B, SIM, RUF), E501 ignored
- **Line length**: 100
- **Target**: Python 3.10+
- **isort**: `capydocs` as known first-party

## CI/CD

- **CI** (`.github/workflows/ci.yml`): Runs lint + test on PR/push to main. Tests against Python 3.10, 3.12, 3.13.
- **Release** (`.github/workflows/release.yml`): Uses [Release Please](https://github.com/googleapis/release-please) on main. Merging a release PR auto-updates `CHANGELOG.md`, bumps version in `pyproject.toml`, creates a GitHub Release, and publishes to PyPI.
- **Commit convention**: [Conventional Commits](https://www.conventionalcommits.org/) — `feat:` (minor), `fix:` (patch), `feat!:` (major).

## Environment

Copy `.env.example` to `.env`. Only variable: `OPENAI_API_KEY` (optional, for AI features).
