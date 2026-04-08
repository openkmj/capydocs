.PHONY: install run dev test lint format build clean

install:
	uv pip install -e ".[dev,ai]"

run:
	uv run capydocs --dir ./docs --port 8000

dev:
	uv run capydocs --dir ./docs --port 8000 --reload

test:
	uv run --extra dev pytest tests/ -v

lint:
	uv run --extra dev ruff check src/ tests/

format:
	uv run --extra dev ruff check --fix src/ tests/

build:
	uv run --extra dev python -m build

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info
