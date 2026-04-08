.PHONY: install run dev test lint format build clean

install:
	uv pip install -e ".[dev,ai]"

run:
	uv run capydocs --dir ./docs --port 8000

dev:
	uv run capydocs --dir ./docs --port 8000 --reload

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff check --fix src/ tests/

build:
	uv run python -m build

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info
