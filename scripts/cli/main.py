#!/usr/bin/env python3
"""Unified CLI for union-search-skill."""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure local module imports work when run as script.
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from adapters import run_defuddle, run_download, run_image, run_platform, run_search
from errors import CliError, CliUsageError
from output import build_envelope, render_output
from registry import IMAGE_PLATFORMS, load_capabilities, load_groups
from validators import parse_param_pairs, resolve_query, validate_platforms

__version__ = "0.1.0"
PLATFORM_COMMAND_ALIASES: Dict[str, List[str]] = {
    "google": ["gsearch"],
    "bing": ["bsearch"],
}


def parse_args() -> argparse.Namespace:
    """Create parser and parse arguments."""
    parser = argparse.ArgumentParser(
        description="union-search unified CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/cli/main.py list --format markdown\n"
            "  python scripts/cli/main.py doctor --env-file .env\n"
            "  python scripts/cli/main.py search \"AI\" --group dev --limit 3 --pretty\n"
            "  python scripts/cli/main.py platform github \"machine learning\" --limit 5 --pretty\n"
            "  python scripts/cli/main.py google \"AI Agent\" --limit 5 --pretty\n"
            "  python scripts/cli/main.py bsearch \"AI Agent\" --limit 5 --pretty\n"
            "  python scripts/cli/main.py image \"cats\" --platforms baidu bing --limit 20 --output-dir ./image_downloads\n"
            "  python scripts/cli/main.py download \"https://www.youtube.com/watch?v=dQw4w9WgXcQ\" --output-dir ./downloads\n"
        ),
    )
    parser.add_argument("--version", action="version", version=f"union-search CLI v{__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # search
    search_parser = subparsers.add_parser("search", help="Aggregated multi-platform search")
    search_parser.add_argument("query", nargs="?", help="Search query")
    search_parser.add_argument("--query", dest="query_opt", help="Search query (overrides positional)")
    search_parser.add_argument("--platforms", "-p", nargs="+", help="Specific platforms")
    search_parser.add_argument("--group", "-g", help="Platform group")
    search_parser.add_argument("--limit", "-l", type=int, default=None, help="Per-platform item limit")
    search_parser.add_argument("--max-workers", type=int, default=5, help="Concurrency")
    search_parser.add_argument("--timeout", type=int, default=60, help="Timeout seconds")
    search_parser.add_argument("--deduplicate", action="store_true", help="Cross-platform deduplicate")
    search_parser.add_argument("--fail-on-platform-error", action="store_true", help="Exit non-zero on partial platform failures")
    search_parser.add_argument("--env-file", default=".env", help="Env file path")
    _add_output_args(search_parser)

    # platform
    platform_parser = subparsers.add_parser("platform", help="Run a single platform")
    platform_parser.add_argument("platform", help="Platform name")
    platform_parser.add_argument("query", nargs="?", help="Search query")
    platform_parser.add_argument("--query", dest="query_opt", help="Search query (overrides positional)")
    platform_parser.add_argument("--limit", "-l", type=int, default=None, help="Result limit")
    platform_parser.add_argument("--timeout", type=int, default=60, help="Timeout seconds")
    platform_parser.add_argument("--param", action="append", help="Adapter passthrough key=value (repeatable)")
    platform_parser.add_argument("--fail-on-platform-error", action="store_true", help="Exit non-zero if platform fails")
    platform_parser.add_argument("--env-file", default=".env", help="Env file path")
    _add_output_args(platform_parser)

    # image
    image_parser = subparsers.add_parser("image", help="Multi-platform image search/download")
    image_parser.add_argument("query", nargs="?", help="Search query")
    image_parser.add_argument("--query", dest="query_opt", help="Search query (overrides positional)")
    image_parser.add_argument("--platforms", "-p", nargs="+", help="Image platforms")
    image_parser.add_argument("--limit", "-l", type=int, default=10, help="Images per platform (<=0 unlimited)")
    image_parser.add_argument("--output-dir", default="image_downloads", help="Output directory")
    image_parser.add_argument("--threads", type=int, default=5, help="Download threads")
    image_parser.add_argument("--delay", type=float, default=1.0, help="Delay between platforms in seconds")
    image_parser.add_argument("--no-metadata", action="store_true", help="Disable metadata output")
    image_parser.add_argument("--env-file", default=".env", help="Env file path")
    image_parser.add_argument("--timeout", type=int, default=1800, help="Command timeout seconds")
    _add_output_args(image_parser)

    # download
    download_parser = subparsers.add_parser("download", help="Download media using yt-dlp")
    download_parser.add_argument("urls", nargs="*", help="Direct media URLs to download")
    download_parser.add_argument("--from-file", help="Load URLs from search result JSON file")
    download_parser.add_argument("--platforms", "-p", nargs="+", help="Filter platforms when using --from-file")
    download_parser.add_argument("--select", help="Select candidate indices from --from-file, e.g. 1,3,5")
    download_parser.add_argument("--limit", "-l", type=int, default=None, help="Max candidates when using --from-file")
    download_parser.add_argument("--output-dir", default="downloads", help="Download output directory")
    download_parser.add_argument("--audio-only", action="store_true", help="Extract audio only")
    download_parser.add_argument("--audio-format", default="mp3", help="Audio format when --audio-only")
    download_parser.add_argument("--media-format", help="yt-dlp format selector, e.g. bestvideo+bestaudio/best")
    download_parser.add_argument("--max-height", type=int, help="Prefer max video height (e.g. 1080)")
    download_parser.add_argument("--cookies-file", help="Path to cookies.txt (Netscape format)")
    download_parser.add_argument("--cookies-from-browser", help="Browser name for cookies import, e.g. chrome")
    download_parser.add_argument("--restrict-filenames", action=argparse.BooleanOptionalAction, default=True, help="Use safe ASCII-ish filenames")
    download_parser.add_argument("--continue-download", action=argparse.BooleanOptionalAction, default=True, help="Resume partial downloads")
    download_parser.add_argument("--retries", type=int, default=None, help="Global retry count for yt-dlp")
    download_parser.add_argument("--fragment-retries", type=int, default=None, help="Retry count for HLS/DASH fragments")
    download_parser.add_argument("--retry-sleep", help="Retry sleep strategy, e.g. fragment:exp=1:10")
    download_parser.add_argument("--proxy", help="Proxy URL, e.g. socks5://127.0.0.1:1080")
    download_parser.add_argument("--timeout", type=int, default=3600, help="Command timeout seconds")
    download_parser.add_argument("--dry-run", action="store_true", help="Resolve metadata without downloading")
    download_parser.add_argument("--fail-on-download-error", action="store_true", help="Exit non-zero if download fails")
    download_parser.add_argument("--env-file", default=".env", help="Env file path")
    _add_output_args(download_parser)

    # list
    list_parser = subparsers.add_parser("list", help="List platform capabilities and groups")
    list_parser.add_argument("--type", choices=["all", "platforms", "groups", "images"], default="all")
    _add_output_args(list_parser)

    # doctor
    doctor_parser = subparsers.add_parser("doctor", help="Run environment and dependency checks")
    doctor_parser.add_argument("--platforms", "-p", nargs="+", help="Only check selected platforms")
    doctor_parser.add_argument("--env-file", default=".env", help="Env file path")
    doctor_parser.add_argument("--strict", action="store_true", help="Return non-zero on warnings")
    _add_output_args(doctor_parser)

    # defuddle - URL to Markdown (special handling because it takes URL not query)
    defuddle_parser = subparsers.add_parser("defuddle", help="Extract web page content to Markdown using Defuddle")
    defuddle_parser.add_argument("url", nargs="?", help="URL to extract content from")
    defuddle_parser.add_argument("--url", dest="url_opt", help="URL to extract (overrides positional)")
    defuddle_parser.add_argument("--json", action="store_true", help="Output JSON with metadata")
    defuddle_parser.add_argument("--timeout", type=int, default=60, help="Timeout seconds")
    defuddle_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    _add_output_args(defuddle_parser)

    # direct platform commands, e.g. `google "query"` / `bing "query"`
    _add_direct_platform_subcommands(subparsers)

    return parser.parse_args()


def _add_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=["json", "markdown", "text"], default="json", help="Output format")
    parser.add_argument("--pretty", action="store_true", help="Pretty JSON")
    parser.add_argument("-o", "--output", help="Write output to file")


def _add_platform_execution_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--query", dest="query_opt", help="Search query (overrides positional)")
    parser.add_argument("--limit", "-l", type=int, default=None, help="Result limit")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout seconds")
    parser.add_argument("--param", action="append", help="Adapter passthrough key=value (repeatable)")
    parser.add_argument("--fail-on-platform-error", action="store_true", help="Exit non-zero if platform fails")
    parser.add_argument("--env-file", default=".env", help="Env file path")
    _add_output_args(parser)


def _add_direct_platform_subcommands(subparsers: argparse._SubParsersAction) -> None:
    """Add direct platform subcommands (excluding defuddle which has special handling)."""
    capabilities = load_capabilities()
    # Defuddle has its own dedicated command with URL-specific arguments
    excluded_platforms = {"defuddle"}
    for cap in capabilities:
        if cap.name in excluded_platforms:
            continue
        aliases = PLATFORM_COMMAND_ALIASES.get(cap.name, [])
        parser = subparsers.add_parser(
            cap.name,
            aliases=aliases,
            help=f"Direct call: {cap.name} ({cap.description})",
        )
        _add_platform_execution_args(parser)
        parser.set_defaults(platform_command=cap.name)


def write_output(content: str, output_path: Optional[str]) -> None:
    if output_path:
        target = Path(output_path)
        if not target.is_absolute():
            target = Path.cwd() / target
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, target)
        print(str(target), file=sys.stderr)
        return
    print(content)


def handle_search(args: argparse.Namespace) -> Dict[str, Any]:
    query = resolve_query(args.query, args.query_opt)
    caps = load_capabilities()
    known = [c.name for c in caps]

    groups = load_groups()
    if args.group and args.group not in groups:
        raise CliUsageError(f"Unknown group '{args.group}'. Available: {', '.join(sorted(groups))}")

    selected_platforms = validate_platforms(args.platforms, known) if args.platforms else None
    data = run_search(
        query=query,
        platforms=selected_platforms,
        group=args.group,
        limit=args.limit,
        max_workers=args.max_workers,
        timeout=args.timeout,
        deduplicate=args.deduplicate,
        env_file=args.env_file,
    )
    failed = int(data.get("summary", {}).get("failed", 0))
    success = failed == 0
    errors: List[Dict[str, Any]] = []
    if failed:
        errors.append({"code": "partial_failure", "message": f"{failed} platforms failed"})
    return {
        "query": query,
        "success": success,
        "data": data,
        "errors": errors,
        "meta": {
            "failed_platforms": failed,
            "selected_platforms": data.get("platforms", []),
            "downloadable_items": len(data.get("download_candidates", [])),
        },
        "runtime_exit_code": 2 if (args.fail_on_platform_error and failed > 0) else 0,
    }


def handle_platform(args: argparse.Namespace) -> Dict[str, Any]:
    query = resolve_query(args.query, args.query_opt)
    caps = load_capabilities()
    known = [c.name for c in caps]
    platform = validate_platforms([args.platform], known)[0]
    return _handle_single_platform_run(platform, query, args, command_name="platform")


def handle_platform_direct(args: argparse.Namespace) -> Dict[str, Any]:
    query = resolve_query(args.query, args.query_opt)
    caps = load_capabilities()
    known = [c.name for c in caps]
    platform = validate_platforms([args.platform_command], known)[0]
    command_name = f"platform:{platform}"
    return _handle_single_platform_run(platform, query, args, command_name=command_name)


def _handle_single_platform_run(
    platform: str,
    query: str,
    args: argparse.Namespace,
    command_name: str,
) -> Dict[str, Any]:
    params = parse_param_pairs(args.param)
    data = run_platform(
        platform=platform,
        query=query,
        limit=args.limit,
        timeout=args.timeout,
        env_file=args.env_file,
        params=params,
    )
    success = bool(data.get("success"))
    errors: List[Dict[str, Any]] = []
    if not success:
        errors.append({"code": "platform_error", "message": str(data.get("error") or "Platform failed")})
    return {
        "command": command_name,
        "query": query,
        "success": success,
        "data": data,
        "errors": errors,
        "meta": {"platform": platform},
        "runtime_exit_code": 2 if (args.fail_on_platform_error and not success) else 0,
    }


def handle_image(args: argparse.Namespace) -> Dict[str, Any]:
    query = resolve_query(args.query, args.query_opt)
    selected_platforms = validate_platforms(args.platforms, IMAGE_PLATFORMS) if args.platforms else None
    data = run_image(
        query=query,
        platforms=selected_platforms,
        limit=args.limit,
        output_dir=args.output_dir,
        threads=args.threads,
        delay=args.delay,
        no_metadata=args.no_metadata,
        env_file=args.env_file,
        timeout=args.timeout,
    )
    summary = data.get("summary", {})
    failed = int(summary.get("failed", 0))
    success = failed == 0
    errors: List[Dict[str, Any]] = []
    if failed:
        errors.append({"code": "partial_failure", "message": f"{failed} image platforms failed"})
    return {
        "query": query,
        "success": success,
        "data": data,
        "errors": errors,
        "meta": {"selected_image_platforms": selected_platforms or list(IMAGE_PLATFORMS)},
        "runtime_exit_code": 0,
    }


def handle_download(args: argparse.Namespace) -> Dict[str, Any]:
    if not args.urls and not args.from_file:
        raise CliUsageError("Provide at least one URL or use --from-file")

    data = run_download(
        urls=args.urls,
        from_file=args.from_file,
        platforms=args.platforms,
        select=args.select,
        limit=args.limit,
        output_dir=args.output_dir,
        audio_only=args.audio_only,
        audio_format=args.audio_format,
        media_format=args.media_format,
        max_height=args.max_height,
        cookies_file=args.cookies_file,
        cookies_from_browser=args.cookies_from_browser,
        restrict_filenames=args.restrict_filenames,
        continue_download=args.continue_download,
        retries=args.retries,
        fragment_retries=args.fragment_retries,
        retry_sleep=args.retry_sleep,
        proxy=args.proxy,
        env_file=args.env_file,
        timeout=args.timeout,
        dry_run=args.dry_run,
    )
    success = bool(data.get("success"))
    errors: List[Dict[str, Any]] = []
    if not success:
        errors.append(
            {
                "code": "download_error",
                "message": str(data.get("stderr") or data.get("stdout") or "yt-dlp download failed"),
            }
        )

    return {
        "query": None,
        "success": success,
        "data": data,
        "errors": errors,
        "meta": {
            "source_file": args.from_file,
            "provided_urls": len(args.urls or []),
            "resolved_urls": len(data.get("resolved_urls", [])),
        },
        "runtime_exit_code": 2 if (args.fail_on_download_error and not success) else 0,
    }


def handle_list(args: argparse.Namespace) -> Dict[str, Any]:
    capabilities = load_capabilities()
    groups = load_groups()
    payload: Dict[str, Any] = {}

    if args.type in {"all", "platforms"}:
        payload["platforms"] = [cap.to_dict() for cap in capabilities]
    if args.type in {"all", "groups"}:
        payload["groups"] = groups
    if args.type in {"all", "images"}:
        payload["image_platforms"] = list(IMAGE_PLATFORMS)

    return {
        "query": None,
        "success": True,
        "data": payload,
        "errors": [],
        "meta": {"count_platforms": len(capabilities), "count_groups": len(groups)},
        "runtime_exit_code": 0,
    }


def handle_doctor(args: argparse.Namespace) -> Dict[str, Any]:
    capabilities = load_capabilities()
    groups = load_groups()
    selected = set(validate_platforms(args.platforms, [c.name for c in capabilities])) if args.platforms else None

    # Best-effort env loading using existing union loader.
    scripts_dir = Path(__file__).resolve().parents[1]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from union_search.union_search import load_env_file

    load_env_file(args.env_file)
    env_path = Path(args.env_file)
    if not env_path.is_absolute():
        env_path = Path.cwd() / env_path

    checks: List[Dict[str, Any]] = []
    checks.append(
        {
            "name": "env_file",
            "status": "pass" if env_path.exists() else "warn",
            "message": f"env file {'found' if env_path.exists() else 'not found'} at {env_path}",
        }
    )

    try:
        import requests  # noqa: F401

        requests_status = "pass"
        requests_message = "requests is installed"
    except Exception:
        requests_status = "fail"
        requests_message = "requests is missing"
    checks.append({"name": "dependency_requests", "status": requests_status, "message": requests_message})

    try:
        import dotenv  # noqa: F401

        dotenv_status = "pass"
        dotenv_message = "python-dotenv is installed"
    except Exception:
        dotenv_status = "fail"
        dotenv_message = "python-dotenv is missing"
    checks.append({"name": "dependency_dotenv", "status": dotenv_status, "message": dotenv_message})

    try:
        import imagedl  # noqa: F401

        image_dep_status = "pass"
        image_dep_message = "pyimagedl is installed"
    except Exception:
        image_dep_status = "warn"
        image_dep_message = "pyimagedl not installed (image command unavailable)"
    checks.append({"name": "dependency_pyimagedl", "status": image_dep_status, "message": image_dep_message})

    ytdlp_path = shutil.which("yt-dlp")
    ytdlp_status = "pass" if ytdlp_path else "warn"
    ytdlp_message = f"yt-dlp found at {ytdlp_path}" if ytdlp_path else "yt-dlp not found (download command unavailable)"
    checks.append({"name": "dependency_ytdlp", "status": ytdlp_status, "message": ytdlp_message})

    ffmpeg_path = shutil.which("ffmpeg")
    ffmpeg_status = "pass" if ffmpeg_path else "warn"
    ffmpeg_message = f"ffmpeg found at {ffmpeg_path}" if ffmpeg_path else "ffmpeg not found (format merge/audio extraction may fail)"
    checks.append({"name": "dependency_ffmpeg", "status": ffmpeg_status, "message": ffmpeg_message})

    platform_checks: List[Dict[str, Any]] = []
    for cap in capabilities:
        if selected and cap.name not in selected:
            continue
        missing = [key for key in cap.required_env if not os.getenv(key)]
        if cap.status == "disabled":
            status = "warn"
            message = cap.notes or "disabled platform"
        elif missing:
            status = "warn"
            message = f"missing required env: {', '.join(missing)}"
        else:
            status = "pass"
            message = "ready"
        platform_checks.append(
            {
                "platform": cap.name,
                "status": status,
                "message": message,
                "required_env": list(cap.required_env),
                "groups": list(cap.groups),
            }
        )

    summary = {
        "checks_pass": len([c for c in checks if c["status"] == "pass"]),
        "checks_warn": len([c for c in checks if c["status"] == "warn"]),
        "checks_fail": len([c for c in checks if c["status"] == "fail"]),
        "platform_pass": len([c for c in platform_checks if c["status"] == "pass"]),
        "platform_warn": len([c for c in platform_checks if c["status"] == "warn"]),
        "platform_total": len(platform_checks),
        "groups_available": sorted(groups.keys()),
    }

    has_fail = summary["checks_fail"] > 0
    has_warn = summary["checks_warn"] > 0 or summary["platform_warn"] > 0
    success = not has_fail and not (args.strict and has_warn)
    errors: List[Dict[str, Any]] = []
    if has_fail:
        errors.append({"code": "dependency_failure", "message": "One or more required dependencies are missing"})
    if args.strict and has_warn:
        errors.append({"code": "strict_warning", "message": "Warnings detected under --strict mode"})

    return {
        "query": None,
        "success": success,
        "data": {"checks": checks, "platforms": platform_checks, "summary": summary},
        "errors": errors,
        "meta": {"env_file": str(env_path)},
        "runtime_exit_code": 2 if not success else 0,
    }


def handle_defuddle(args: argparse.Namespace) -> Dict[str, Any]:
    """Handle defuddle URL to Markdown command."""
    from url_to_markdown.engines.defuddle_engine import DefuddleEngine

    # Resolve URL from positional or --url argument
    url = args.url or args.url_opt
    if not url:
        raise CliUsageError("URL is required for defuddle command. Use: defuddle <url> or defuddle --url <url>")

    started = datetime.now()
    try:
        client = DefuddleEngine(timeout=args.timeout)
        result = client.fetch(
            url=url,
            markdown=True,
            json_output=args.json,
            timeout=args.timeout,
        )
        success = True
        errors: List[Dict[str, Any]] = []
    except Exception as exc:
        result = {"error": str(exc)}
        success = False
        errors = [{"code": "defuddle_error", "message": str(exc)}]

    duration_ms = int((datetime.now() - started).total_seconds() * 1000)
    result["adapter_timing_ms"] = duration_ms

    return {
        "command": "defuddle",
        "query": url,
        "success": success,
        "data": result,
        "errors": errors,
        "meta": {"url": url},
        "runtime_exit_code": 0 if success else 2,
    }


def dispatch(args: argparse.Namespace) -> Dict[str, Any]:
    if hasattr(args, "platform_command"):
        return handle_platform_direct(args)
    if args.command == "search":
        return handle_search(args)
    if args.command == "platform":
        return handle_platform(args)
    if args.command == "image":
        return handle_image(args)
    if args.command == "download":
        return handle_download(args)
    if args.command == "list":
        return handle_list(args)
    if args.command == "doctor":
        return handle_doctor(args)
    if args.command == "defuddle":
        return handle_defuddle(args)
    raise CliUsageError(f"Unknown command: {args.command}")


def main() -> int:
    started_at = datetime.now()
    try:
        args = parse_args()
        result = dispatch(args)
        envelope = build_envelope(
            command=str(result.get("command", args.command)),
            query=result.get("query"),
            started_at=started_at,
            success=bool(result.get("success")),
            data=result.get("data"),
            errors=result.get("errors"),
            meta=result.get("meta"),
        )
        rendered = render_output(envelope, fmt=args.format, pretty=bool(args.pretty))
        write_output(rendered, args.output)
        return int(result.get("runtime_exit_code", 0))
    except CliError as exc:
        envelope = build_envelope(
            command="error",
            query=None,
            started_at=started_at,
            success=False,
            data={},
            errors=[
                {
                    "code": exc.__class__.__name__,
                    "message": exc.message,
                    "detail": exc.detail,
                }
            ],
            meta={},
        )
        print(render_output(envelope, fmt="json", pretty=True), file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
