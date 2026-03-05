#!/usr/bin/env python3
"""Execution adapters for unified CLI commands."""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from errors import CliRuntimeError


def _ensure_scripts_on_path() -> None:
    scripts_dir = Path(__file__).resolve().parents[1]
    scripts_path = str(scripts_dir)
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)


def _extract_json_from_text(text: str) -> Any:
    """Extract first JSON object/array from noisy text."""
    if not text:
        raise ValueError("Empty output")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text):
        if ch not in "[{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[idx:])
            return obj
        except json.JSONDecodeError:
            continue

    raise ValueError("No valid JSON found in output")


def run_search(
    query: str,
    platforms: Optional[List[str]],
    group: Optional[str],
    limit: Optional[int],
    max_workers: int,
    timeout: int,
    deduplicate: bool,
    env_file: str,
) -> Dict[str, Any]:
    """Run aggregated multi-platform search."""
    _ensure_scripts_on_path()
    from union_search.union_search import (
        PLATFORM_GROUPS,
        PLATFORM_MODULES,
        load_env_file,
        union_search,
    )

    load_env_file(env_file)

    if platforms:
        selected = list(platforms)
    elif group:
        if group not in PLATFORM_GROUPS:
            raise CliRuntimeError(f"Unknown platform group: {group}")
        selected = list(PLATFORM_GROUPS[group])
    else:
        selected = list(PLATFORM_GROUPS["all"])

    invalid = [p for p in selected if p not in PLATFORM_MODULES]
    if invalid:
        raise CliRuntimeError(f"Invalid platforms for union search: {', '.join(invalid)}")

    started = datetime.now()
    result = union_search(
        keyword=query,
        platforms=selected,
        limit=limit,
        max_workers=max_workers,
        timeout=timeout,
        deduplicate=deduplicate,
    )
    duration_ms = int((datetime.now() - started).total_seconds() * 1000)
    result["adapter_timing_ms"] = duration_ms
    return result


def run_platform(
    platform: str,
    query: str,
    limit: Optional[int],
    timeout: int,
    env_file: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run a single platform search through union adapter."""
    _ensure_scripts_on_path()
    from union_search.union_search import PLATFORM_MODULES, load_env_file, search_platform

    if platform not in PLATFORM_MODULES:
        raise CliRuntimeError(f"Unknown platform: {platform}")

    load_env_file(env_file)
    extra = dict(params or {})

    started = datetime.now()
    try:
        _, result = search_platform(
            platform=platform,
            keyword=query,
            limit=limit,
            timeout=timeout,
            **extra,
        )
    except Exception as exc:
        raise CliRuntimeError(f"Platform execution failed: {exc}") from exc

    duration_ms = int((datetime.now() - started).total_seconds() * 1000)
    result["adapter_timing_ms"] = duration_ms
    return result


def run_image(
    query: str,
    platforms: Optional[List[str]],
    limit: int,
    output_dir: str,
    threads: int,
    delay: float,
    no_metadata: bool,
    env_file: str,
    timeout: int,
) -> Dict[str, Any]:
    """Run image search script through subprocess and parse JSON result."""
    script_path = Path(__file__).resolve().parents[1] / "union_image_search" / "multi_platform_image_search.py"
    cmd: List[str] = [
        sys.executable,
        str(script_path),
        "--keyword",
        query,
        "--num",
        str(limit),
        "--output",
        output_dir,
        "--threads",
        str(threads),
        "--delay",
        str(delay),
        "--env-file",
        env_file,
        "--pretty",
    ]
    if no_metadata:
        cmd.append("--no-metadata")
    if platforms:
        cmd.extend(["--platforms", *platforms])

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip() or f"exit code {proc.returncode}"
        raise CliRuntimeError(f"Image command failed: {detail}")

    try:
        parsed = _extract_json_from_text(proc.stdout)
    except Exception as exc:
        raise CliRuntimeError(f"Failed to parse image command output: {exc}") from exc

    # Keep stderr for diagnostics; scripts print progress there in some environments.
    if proc.stderr.strip():
        parsed["_stderr"] = proc.stderr.strip()
    return parsed
