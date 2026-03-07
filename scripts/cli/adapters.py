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
    from downloader.yt_dlp_downloader import build_download_candidates
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
    download_candidates = build_download_candidates(result)
    result["download_candidates"] = download_candidates
    summary = result.get("summary")
    if isinstance(summary, dict):
        summary["downloadable_items"] = len(download_candidates)
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


def run_defuddle(
    url: str,
    markdown: bool = True,
    json_output: bool = False,
    debug: bool = False,
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Run Defuddle to extract web page content.

    Args:
        url: URL to extract content from
        markdown: Whether to output in Markdown format
        json_output: Whether to output JSON with metadata
        debug: Enable debug mode
        timeout: Request timeout in seconds

    Returns:
        Dictionary containing title, content, url and optionally metadata
    """
    _ensure_scripts_on_path()
    from url_to_markdown.engines.defuddle_engine import DefuddleEngine

    started = datetime.now()

    try:
        client = DefuddleEngine(timeout=timeout)
        result = client.fetch(
            url=url,
            markdown=markdown,
            json_output=json_output,
            timeout=timeout,
        )
    except Exception as exc:
        raise CliRuntimeError(f"Defuddle failed: {exc}") from exc

    duration_ms = int((datetime.now() - started).total_seconds() * 1000)
    result["adapter_timing_ms"] = duration_ms
    return result


def run_download(
    urls: Optional[List[str]],
    from_file: Optional[str],
    platforms: Optional[List[str]],
    select: Optional[str],
    limit: Optional[int],
    output_dir: str,
    audio_only: bool,
    audio_format: str,
    media_format: Optional[str],
    max_height: Optional[int],
    cookies_file: Optional[str],
    cookies_from_browser: Optional[str],
    restrict_filenames: bool,
    continue_download: bool,
    retries: Optional[int],
    fragment_retries: Optional[int],
    retry_sleep: Optional[str],
    proxy: Optional[str],
    env_file: str,
    timeout: int,
    dry_run: bool,
) -> Dict[str, Any]:
    """Run yt-dlp download command and return normalized output."""
    _ensure_scripts_on_path()
    from downloader.yt_dlp_downloader import (
        collect_urls_from_search_output,
        load_env_file,
        run_yt_dlp_download,
    )

    load_env_file(env_file)

    candidates: List[Dict[str, Any]] = []
    resolved_urls: List[str] = list(urls or [])
    if from_file:
        try:
            candidates = collect_urls_from_search_output(
                from_file=from_file,
                platforms=platforms,
                select=select,
                limit=limit,
            )
        except Exception as exc:
            raise CliRuntimeError(f"Failed to load download candidates: {exc}") from exc
        resolved_urls.extend([c["url"] for c in candidates])

    # Stable dedupe while preserving input order.
    deduped_urls = list(dict.fromkeys(url.strip() for url in resolved_urls if url and url.strip()))

    started = datetime.now()
    try:
        result = run_yt_dlp_download(
            urls=deduped_urls,
            output_dir=output_dir,
            audio_only=audio_only,
            audio_format=audio_format,
            media_format=media_format,
            max_height=max_height,
            cookies_file=cookies_file,
            cookies_from_browser=cookies_from_browser,
            restrict_filenames=restrict_filenames,
            continue_download=continue_download,
            retries=retries,
            fragment_retries=fragment_retries,
            retry_sleep=retry_sleep,
            proxy=proxy,
            timeout=timeout,
            dry_run=dry_run,
        )
    except Exception as exc:
        raise CliRuntimeError(f"Download execution failed: {exc}") from exc

    duration_ms = int((datetime.now() - started).total_seconds() * 1000)
    result["adapter_timing_ms"] = duration_ms
    result["candidates"] = candidates
    result["resolved_urls"] = deduped_urls
    return result
