"""CLI entry point for capydocs."""

import json
import os
import sys
from pathlib import Path

import click
import uvicorn

try:
    import tomllib
except ImportError:
    import tomli as tomllib


def _load_config(config_path: str | None) -> dict:
    """Load capydocs.toml config file."""
    if config_path:
        config_file = Path(config_path)
        if not config_file.is_file():
            click.echo(f"Error: config file not found: {config_path}", err=True)
            sys.exit(1)
    else:
        config_file = Path("capydocs.toml")

    if config_file.is_file():
        with open(config_file, "rb") as f:
            return tomllib.load(f)
    return {}


@click.command()
@click.option("--config", "config_path", default=None, help="Path to capydocs.toml config file")
@click.option("--port", default=None, type=int, help="Port to run the server on")
@click.option("--host", default="0.0.0.0", help="Host to bind the server to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def main(config_path: str | None, port: int | None, host: str, reload: bool) -> None:
    """capydocs - A lightweight web-based markdown document manager."""
    config = _load_config(config_path)

    # Resolve root dirs
    if "dirs" in config:
        root_dirs = {}
        for d in config["dirs"]:
            name = d["name"]
            path = os.path.abspath(os.path.expanduser(d["path"]))
            if not Path(path).is_dir():
                click.echo(f"Warning: directory not found: {path}", err=True)
            root_dirs[name] = path
    else:
        root_dirs = {"": os.path.abspath(".")}

    # Port: CLI flag > config > default
    if port is None:
        port = config.get("port", 8000)

    # Load .env
    env_dirs = [Path(p) for p in root_dirs.values()] + [Path(".")]
    for env_dir in env_dirs:
        env_path = env_dir / ".env"
        if env_path.is_file():
            from dotenv import load_dotenv

            load_dotenv(env_path)
            break

    os.environ["CAPYDOCS_ROOT_DIRS"] = json.dumps(root_dirs)

    click.echo(f"capydocs v0.3.0 serving {len(root_dirs)} dir(s)")
    for name, path in root_dirs.items():
        click.echo(f"  {name or '(root)'}: {path}")
    click.echo(f"Open http://{host}:{port} in your browser")

    uvicorn.run(
        "capydocs.server:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
    )
