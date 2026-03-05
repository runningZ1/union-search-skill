#!/usr/bin/env python3
"""Top-level entrypoint for unified union-search CLI."""

from pathlib import Path
import sys


def _bootstrap() -> None:
    root = Path(__file__).resolve().parent
    cli_dir = root / "scripts" / "cli"
    if str(cli_dir) not in sys.path:
        sys.path.insert(0, str(cli_dir))


def main() -> int:
    _bootstrap()
    from main import main as cli_main

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
