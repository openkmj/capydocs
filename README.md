# capydocs

A lightweight, pip-installable web-based markdown document manager. Point it at any directory and manage your `.md` files through a clean dark-themed web UI with AI-powered text refinement.

## Features

- **File tree** — Browse `.md` files in a collapsible sidebar tree view
- **CodeMirror 6 editor** — Syntax-highlighted markdown editing with formatting toolbar (bold, italic, heading, link, list)
- **Full CRUD + Move** — Create, read, update, delete, and rename/move markdown files
- **Folder management** — Create and delete folders from the sidebar (+ Folder button, hover ✕ to delete, right-click context menu)
- **Drag and drop** — Move files between folders by dragging in the sidebar tree
- **Server-side search** — Search by filename and content with context snippets
- **AI text refinement** — Select text and refine it with OpenAI gpt-5-mini (concise, fix grammar, translate, change tone, or custom instructions)
- **MCP server** — Expose document management as MCP tools for AI agents
- **Keyboard shortcuts** — Ctrl/Cmd+S to save
- **Zero config** — `pip install` and run, no build step or database needed

## Quick Start

### Prerequisites
- Python 3.10+
- (Optional) OpenAI API key for AI features

### Installation & Run

```bash
# Install
pip install -e ".[ai]"

# Create a .env file with your OpenAI key (optional, for AI features)
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Serve a directory
capydocs --dir ./docs

# Open http://localhost:8000 in your browser
```

### CLI Options

```
capydocs [OPTIONS]

Options:
  --dir TEXT      Root directory to serve (default: current directory)
  --port INTEGER  Port number (default: 8000)
  --host TEXT     Host to bind to (default: 0.0.0.0)
  --reload        Enable auto-reload for development
  --help          Show help message
```

### Development Commands (Makefile)

```bash
make install    # pip install -e ".[dev,ai]"
make run        # Start server (port 8000)
make dev        # Start with auto-reload
make test       # Run pytest
make lint       # Run ruff check
make format     # Run ruff --fix
make build      # Build package (dist/)
make clean      # Remove build artifacts
```

## AI Features

AI text refinement uses OpenAI gpt-5-mini. Set your API key in `.env`:

```bash
OPENAI_API_KEY=sk-...
```

### Usage
1. Open a file in the editor
2. Select text you want to refine
3. Click the **AI** button in the toolbar
4. Choose a preset or type a custom instruction
5. Preview the result and click **Apply**

### Presets

| Preset | Description |
|--------|-------------|
| Concise | Make text more concise |
| Fix grammar | Fix spelling and punctuation |
| English | Translate to English |
| Korean | Translate to Korean |
| Formal | Professional tone |
| Casual | Friendly tone |

## Architecture

```
capydocs/
├── pyproject.toml              # Package metadata + CLI entry point
├── Makefile                    # Dev commands
├── src/capydocs/
│   ├── __init__.py             # Version
│   ├── cli.py                  # Click CLI + .env loading
│   ├── server.py               # FastAPI app factory
│   ├── mcp_server.py           # MCP server (FastMCP)
│   ├── routers/
│   │   ├── files.py            # File CRUD (GET/POST/PUT/DELETE)
│   │   ├── search.py           # Search endpoint
│   │   └── ai.py               # AI refinement endpoint
│   ├── services/
│   │   ├── filesystem.py       # File I/O + path traversal protection
│   │   ├── search.py           # Filename + content search
│   │   └── ai.py               # OpenAI gpt-5-mini integration
│   └── static/
│       ├── index.html          # SPA entry point
│       ├── css/style.css       # Dark theme (Catppuccin-inspired)
│       └── js/
│           ├── app.js          # Main app logic + toast notifications
│           ├── tree.js         # File tree component
│           ├── editor.js       # CodeMirror 6 wrapper
│           ├── ai.js           # AI refinement dialog UI
│           └── cm-bundle.js    # Pre-built CodeMirror bundle
└── tests/                      # 42 tests (pytest)
    ├── conftest.py
    ├── test_filesystem.py
    ├── test_files_api.py
    ├── test_search.py
    └── test_ai.py
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + uvicorn |
| Frontend | Vanilla JS + CodeMirror 6 (pre-built bundle) |
| CLI | Click + python-dotenv |
| AI | OpenAI SDK (gpt-5-mini) |
| Testing | pytest + httpx |
| Linting | ruff (E, F, I, UP, B, SIM, RUF) |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tree` | File tree |
| GET | `/api/files/{path}` | Read file |
| PUT | `/api/files/{path}` | Update file |
| POST | `/api/files/{path}` | Create file |
| PATCH | `/api/files/{path}` | Move/rename file |
| DELETE | `/api/files/{path}` | Delete file |
| POST | `/api/dirs/{path}` | Create directory |
| DELETE | `/api/dirs/{path}` | Delete directory |
| GET | `/api/search?q=` | Search files |
| POST | `/api/ai/refine` | AI text refinement |
| GET | `/api/ai/presets` | List AI presets |

## Design Decisions

- **No build step for frontend** — CodeMirror is pre-bundled via esbuild and shipped as a static asset. No npm/webpack needed at runtime.
- **File-system backed** — No database. Files are read/written directly to disk. What you see in the UI is what's on disk.
- **Path traversal protection** — All file paths are resolved and validated against the root directory before any I/O operation.
- **AI as optional** — Core editing works without any API key. AI features show a clear error message when no key is configured.
- **pip-installable** — Single `pip install` gives you a CLI tool. No Docker, no config files required.
- **Dark theme** — Catppuccin-inspired color scheme for comfortable long-session editing.

## Security

- Path traversal attacks are blocked by resolving all paths and verifying they stay within the configured root directory
- API keys are loaded from environment variables or `.env` files, never exposed to the frontend
- The AI refinement endpoint proxies requests through the server so client never sees the API key

## License

MIT
