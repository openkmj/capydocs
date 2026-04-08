"""CLI entry point for capydocs."""

import click
import uvicorn


@click.command()
@click.option("--dir", "root_dir", default=".", help="Root directory to serve markdown files from")
@click.option("--port", default=8000, help="Port to run the server on")
@click.option("--host", default="0.0.0.0", help="Host to bind the server to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def main(root_dir: str, port: int, host: str, reload: bool) -> None:
    """capydocs - A lightweight web-based markdown document manager."""
    import os
    from pathlib import Path

    # Load .env from the root_dir or current directory
    for env_path in [Path(root_dir) / ".env", Path(".env")]:
        if env_path.is_file():
            from dotenv import load_dotenv

            load_dotenv(env_path)
            break

    os.environ["DOCPYBARA_ROOT_DIR"] = os.path.abspath(root_dir)

    click.echo(f"capydocs v0.1.0 serving '{os.path.abspath(root_dir)}'")
    click.echo(f"Open http://{host}:{port} in your browser")

    uvicorn.run(
        "capydocs.server:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
    )
