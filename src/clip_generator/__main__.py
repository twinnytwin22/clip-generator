"""CLI entry point for the Clip Generator API."""

from __future__ import annotations

import argparse
import uvicorn


def main(argv: list[str] | None = None) -> None:
    """Run the FastAPI server."""
    parser = argparse.ArgumentParser(description="Run the Clip Generator API")
    parser.add_argument("--host", default="0.0.0.0", help="Bind socket to this host")
    parser.add_argument("--port", type=int, default=8000, help="Bind socket to this port")
    args = parser.parse_args(argv)

    uvicorn.run("clip_generator.app.main:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
