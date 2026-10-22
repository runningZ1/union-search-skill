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
from errors import ERROR_REGISTRY, EXIT_INTERNAL, EXIT_INTERRUPTED, CliError, CliUsageError
from output import SCHEMA_VERSION, build_envelope, render_output
from registry import IMAGE_PLATFORMS, load_capabilities, load_groups
from validators import parse_param_pairs, resolve_limit, resolve_query, validate_platforms

__version__ = "0.2.0"

# --quiet / --no-color 写在子命令前时，子解析器会把父解析器的值重置为默认值。
# 解析前先独立扫描一次，结果放这里，供错误路径读取。
_GLOBAL_FLAGS = {"quiet": False, "no_color": False}
PLATFORM_COMMAND_ALIASES: Dict[str, List[str]] = {
    "google": ["gsearch"],
    "bing": ["bsearch"],
}


class _EnvelopeArgumentParser(argparse.ArgumentParser):
    """参数错误改为抛出 CliUsageError，由 main 统一输出错误信封。"""

    def error(self, message: str) -> None:
        code = "UNKNOWN_COMMAND" if message.startswith("argument command") else "INVALID_ARGUMENT"
        raise CliUsageError(message, code=code)

    def exit(self, status: int = 0, message: Optional[str] = None) -> None:
        if status == 0:
            # --help 与 --version 走正常退出
            raise SystemExit(0)
        raise CliUsageError(message or "Invalid arguments", code="INVALID_ARGUMENT")


def parse_args() -> argparse.Namespace:
    """Create parser and parse arguments."""
    common = _EnvelopeArgumentParser(add_help=False, allow_abbrev=False)
    common.add_argument("--quiet", action="store_true", help="Suppress diagnostics on stderr; stdout result is unchanged")
    common.add_argument("--no-color", action="store_true", help="Disable color in human-readable output")

    parser = _EnvelopeArgumentParser(
        description="union-search unified CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
        parents=[common],
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
    search_parser = subparsers.add_parser("search", help="Aggregated multi-platform search", parents=[common])
    search_parser.add_argument("query", nargs="?", help="Search query")
    search_parser.add_argument("--query", dest="query_opt", help="Search query (overrides positional)")
    search_parser.add_argument("--platforms", "-p", nargs="+", help="Specific platforms")
    search_parser.add_argument("--group", "-g", help="Platform group: general (default, no required API key), api, dev, social, preferred, tools, all; aliases: search/no_api_key")
    search_parser.add_argument("--limit", "-l", type=int, default=None, help="Per-platform item limit")
    search_parser.add_argument("--preset", choices=["small", "medium", "large", "extra"], help="Predefined result limits (small=3, medium=5, large=10, extra=20)")
    search_parser.add_argument("--max-workers", type=int, default=5, help="Concurrency")
    search_parser.add_argument("--timeout", type=int, default=60, help="Timeout seconds")
    search_parser.add_argument("--deduplicate", action="store_true", help="Cross-platform deduplicate")
    search_parser.add_argument("--fail-on-platform-error", action="store_true", help="Exit non-zero on partial platform failures")
    search_parser.add_argument("--env-file", default=".env", help="Env file path")
    _add_output_args(search_parser)

    # platform
    platform_parser = subparsers.add_parser("platform", help="Run a single platform", parents=[common])
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
    image_parser = subparsers.add_parser("image", help="Multi-platform image search/download", parents=[common])
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
    download_parser = subparsers.add_parser("download", help="Download media using yt-dlp", parents=[common])
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
    list_parser = subparsers.add_parser("list", help="List platform capabilities and groups", parents=[common])
    list_parser.add_argument("--type", choices=["all", "platforms", "groups", "images"], default="all")
    _add_output_args(list_parser)

    # schema：机器可读的能力描述
    schema_parser = subparsers.add_parser("schema", help="Print the machine-readable capability schema", parents=[common])
    _add_output_args(schema_parser)

    # errors：错误码与退出码注册表
    errors_parser = subparsers.add_parser("errors", help="Print the error code and exit code registry", parents=[common])
    _add_output_args(errors_parser)

    # doctor
    doctor_parser = subparsers.add_parser("doctor", help="Run environment and dependency checks", parents=[common])
    doctor_parser.add_argument("--platforms", "-p", nargs="+", help="Only check selected platforms")
    doctor_parser.add_argument("--env-file", default=".env", help="Env file path")
    doctor_parser.add_argument("--strict", action="store_true", help="Return non-zero on warnings")
    _add_output_args(doctor_parser)

    # defuddle - URL to Markdown (special handling because it takes URL not query)
    defuddle_parser = subparsers.add_parser("defuddle", help="Extract web page content to Markdown using Defuddle", parents=[common])
    defuddle_parser.add_argument("url", nargs="?", help="URL to extract content from")
    defuddle_parser.add_argument("--url", dest="url_opt", help="URL to extract (overrides positional)")
    defuddle_parser.add_argument("--json", action="store_true", help="Output JSON with metadata")
    defuddle_parser.add_argument("--timeout", type=int, default=60, help="Timeout seconds")
    defuddle_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    _add_output_args(defuddle_parser)

    # direct platform commands, e.g. `google "query"` / `bing "query"`
    _add_direct_platform_subcommands(subparsers, common)

    # --quiet 写在子命令前时，子解析器会把它重置为默认值 False，所以先独立扫一遍。
    # 这一步必须在 parse_args 之前：未知命令会让解析直接抛错。
    scanner = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    scanner.add_argument("--quiet", action="store_true")
    scanner.add_argument("--no-color", action="store_true")
    preliminary, _ = scanner.parse_known_args()
    _GLOBAL_FLAGS["quiet"] = preliminary.quiet
    _GLOBAL_FLAGS["no_color"] = preliminary.no_color
    args = parser.parse_args()
    args.quiet = args.quiet or preliminary.quiet
    args.no_color = args.no_color or preliminary.no_color
    return args


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


def _add_direct_platform_subcommands(subparsers: argparse._SubParsersAction, common: argparse.ArgumentParser) -> None:
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
            parents=[common],
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
    limit = resolve_limit(args.limit, args.preset)
    caps = load_capabilities()
    known = [c.name for c in caps]

    groups = load_groups()
    if args.group and args.group not in groups:
        raise CliUsageError(
            f"Unknown group '{args.group}'. Available: {', '.join(sorted(groups))}",
            code="UNKNOWN_GROUP",
            details={"group": args.group, "available": sorted(groups)},
        )

    selected_platforms = validate_platforms(args.platforms, known) if args.platforms else None
    data = run_search(
        query=query,
        platforms=selected_platforms,
        group=args.group,
        limit=limit,
        max_workers=args.max_workers,
        timeout=args.timeout,
        deduplicate=args.deduplicate,
        env_file=args.env_file,
    )
    failed = int(data.get("summary", {}).get("failed", 0))
    success = failed == 0
    errors: List[Dict[str, Any]] = []
    if failed:
        errors.append(
            {
                "code": "PARTIAL_FAILURE",
                "message": f"{failed} platforms failed",
                "retryable": True,
                "outcome": "unknown",
                "next_actions": [{"command": "union-search doctor"}],
            }
        )
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
        "runtime_exit_code": 4 if (args.fail_on_platform_error and failed > 0) else 0,
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
        errors.append(
            {
                "code": "PLATFORM_FAILURE",
                "message": str(data.get("error") or "Platform failed"),
                "retryable": True,
                "outcome": "unknown",
                "next_actions": [{"command": f"union-search doctor --platforms {platform}"}],
            }
        )
    return {
        "command": command_name,
        "query": query,
        "success": success,
        "data": data,
        "errors": errors,
        "meta": {"platform": platform},
        "runtime_exit_code": 4 if (args.fail_on_platform_error and not success) else 0,
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
        errors.append(
            {
                "code": "PARTIAL_FAILURE",
                "message": f"{failed} image platforms failed",
                "retryable": True,
                "outcome": "unknown",
                "next_actions": [{"command": "union-search doctor"}],
            }
        )
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
        raise CliUsageError(
            "Provide at least one URL or use --from-file",
            details={"example": 'union-search download "https://example.com/video" --output-dir ./downloads'},
        )

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
                "code": "DOWNLOAD_FAILURE",
                "message": str(data.get("stderr") or data.get("stdout") or "yt-dlp download failed"),
                "retryable": True,
                "outcome": "unknown",
                "next_actions": [{"command": "union-search doctor"}],
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
        "runtime_exit_code": 4 if (args.fail_on_download_error and not success) else 0,
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


def handle_schema(args: argparse.Namespace) -> Dict[str, Any]:
    """机器可读的能力描述，结构事实来自注册表。"""
    capabilities = load_capabilities()
    groups = load_groups()
    commands = [
        {"name": "search", "effect": "read", "is_idempotent": True, "description": "多平台聚合搜索"},
        {"name": "platform", "effect": "read", "is_idempotent": True, "description": "单平台搜索"},
        {"name": "image", "effect": "write", "is_idempotent": False, "description": "多平台图片搜索与下载"},
        {"name": "download", "effect": "write", "is_idempotent": False, "dry_run": True, "description": "使用 yt-dlp 下载视频或音频"},
        {"name": "defuddle", "effect": "read", "is_idempotent": True, "description": "把网页提取为 Markdown"},
        {"name": "list", "effect": "read", "is_idempotent": True, "description": "列出平台、分组和图片平台"},
        {"name": "schema", "effect": "read", "is_idempotent": True, "description": "输出能力 schema"},
        {"name": "errors", "effect": "read", "is_idempotent": True, "description": "输出错误码与退出码注册表"},
        {"name": "doctor", "effect": "read", "is_idempotent": True, "description": "检查环境、依赖和凭据"},
    ]
    return {
        "query": None,
        "success": True,
        "data": {
            "schema_version": SCHEMA_VERSION,
            "cli_version": __version__,
            "commands": commands,
            "platforms": [cap.to_dict() for cap in capabilities],
            "groups": groups,
            "image_platforms": list(IMAGE_PLATFORMS),
            "limits": {"presets": {"small": 3, "medium": 5, "large": 10, "extra": 20}, "default_search_platforms": "general"},
            "output": {"default": "json", "formats": ["json", "markdown", "text"], "stdout": "envelope only", "stderr": "diagnostics"},
            "errors": ERROR_REGISTRY,
        },
        "errors": [],
        "meta": {"platform_count": len(capabilities)},
        "runtime_exit_code": 0,
    }


def handle_errors(args: argparse.Namespace) -> Dict[str, Any]:
    """输出错误码与退出码注册表。"""
    return {
        "query": None,
        "success": True,
        "data": {
            "schema_version": SCHEMA_VERSION,
            "exit_codes": {
                "0": "success",
                "1": "internal",
                "2": "usage",
                "3": "unavailable",
                "4": "transient",
                "130": "interrupted",
            },
            "errors": ERROR_REGISTRY,
        },
        "errors": [],
        "meta": {},
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

    node_path = shutil.which("node")
    node_status = "pass" if node_path else "warn"
    node_message = f"node found at {node_path}" if node_path else "Node.js not found (defuddle/wechat modules may fail)"
    checks.append({"name": "dependency_node", "status": node_status, "message": node_message})

    npm_path = shutil.which("npm")
    npm_status = "pass" if npm_path else "warn"
    npm_message = f"npm found at {npm_path}" if npm_path else "npm not found (cannot install Node.js dependencies)"
    checks.append({"name": "dependency_npm", "status": npm_status, "message": npm_message})

    # Check for critical npm modules if node is available
    if node_path:
        # Check root node_modules for cheerio and commander
        root_dir = Path(__file__).resolve().parents[2]
        cheerio_path = root_dir / "node_modules" / "cheerio"
        commander_path = root_dir / "node_modules" / "commander"
        
        checks.append({
            "name": "npm_module_cheerio",
            "status": "pass" if cheerio_path.exists() else "fail",
            "message": "cheerio is installed" if cheerio_path.exists() else "cheerio is missing (required for wechat). Run 'npm install'"
        })
        checks.append({
            "name": "npm_module_commander",
            "status": "pass" if commander_path.exists() else "fail",
            "message": "commander is installed" if commander_path.exists() else "commander is missing (required for defuddle). Run 'npm install'"
        })
        
        jsdom_path = root_dir / "node_modules" / "jsdom"
        checks.append({
            "name": "npm_module_jsdom",
            "status": "pass" if jsdom_path.exists() else "fail",
            "message": "jsdom is installed" if jsdom_path.exists() else "jsdom is missing (required for defuddle). Run 'npm install'"
        })
        
        # Check defuddle-node build
        defuddle_dist = root_dir / "scripts" / "url_to_markdown" / "engines" / "defuddle-node" / "dist" / "cli.js"
        checks.append({
            "name": "defuddle_build",
            "status": "pass" if defuddle_dist.exists() else "fail",
            "message": "defuddle-node build found" if defuddle_dist.exists() else "defuddle-node build missing. Run 'npm install' in scripts/url_to_markdown/engines/defuddle-node"
        })

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
        errors.append(
            {
                "code": "MISSING_DEPENDENCY",
                "message": "One or more required dependencies are missing",
                "retryable": False,
                "outcome": "not_started",
                "next_actions": [{"command": "pip install -r requirements.txt"}],
            }
        )
    if args.strict and has_warn:
        errors.append(
            {
                "code": "MISSING_DEPENDENCY",
                "message": "Warnings detected under --strict mode",
                "retryable": False,
                "outcome": "not_started",
                "next_actions": [{"command": "union-search doctor"}],
            }
        )

    return {
        "query": None,
        "success": success,
        "data": {"checks": checks, "platforms": platform_checks, "summary": summary},
        "errors": errors,
        "meta": {"env_file": str(env_path)},
        "runtime_exit_code": 3 if not success else 0,
    }


def handle_defuddle(args: argparse.Namespace) -> Dict[str, Any]:
    """Handle defuddle URL to Markdown command."""
    from url_to_markdown.engines.defuddle_engine import DefuddleEngine

    # Resolve URL from positional or --url argument
    url = args.url or args.url_opt
    if not url:
        raise CliUsageError(
            "URL is required for defuddle command. Use: defuddle <url> or defuddle --url <url>",
            details={"example": "union-search defuddle https://example.com"},
        )

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
        errors = [
            {
                "code": "PLATFORM_FAILURE",
                "message": str(exc),
                "retryable": True,
                "outcome": "not_committed",
                "next_actions": [{"command": "union-search doctor"}],
            }
        ]

    duration_ms = int((datetime.now() - started).total_seconds() * 1000)
    result["adapter_timing_ms"] = duration_ms

    return {
        "command": "defuddle",
        "query": url,
        "success": success,
        "data": result,
        "errors": errors,
        "meta": {"url": url},
        "runtime_exit_code": 0 if success else 4,
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
    if args.command == "schema":
        return handle_schema(args)
    if args.command == "errors":
        return handle_errors(args)
    if args.command == "doctor":
        return handle_doctor(args)
    if args.command == "defuddle":
        return handle_defuddle(args)
    raise CliUsageError(f"Unknown command: {args.command}")


def main() -> int:
    started_at = datetime.now()
    args = argparse.Namespace(quiet=False, no_color=False)
    try:
        args = parse_args()
        if args.no_color:
            os.environ["NO_COLOR"] = "1"
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
            errors=[exc.to_dict()],
            meta={},
        )
        # 机器模式下 stdout 只放信封，诊断信息走 stderr
        print(render_output(envelope, fmt="json", pretty=False))
        if not (getattr(args, "quiet", False) or _GLOBAL_FLAGS["quiet"]):
            print(f"[{exc.code}] {exc.message}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        envelope = build_envelope(
            command="error",
            query=None,
            started_at=started_at,
            success=False,
            data={},
            errors=[{"code": "INTERRUPTED", "message": "Interrupted", "retryable": False, "outcome": "unknown"}],
            meta={},
        )
        print(render_output(envelope, fmt="json", pretty=False))
        return EXIT_INTERRUPTED
    except Exception as exc:  # 未预期的异常统一归为内部错误，避免裸回溯污染 stdout
        envelope = build_envelope(
            command="error",
            query=None,
            started_at=started_at,
            success=False,
            data={},
            errors=[{"code": "INTERNAL_ERROR", "message": f"{type(exc).__name__}: {exc}", "retryable": False, "outcome": "unknown"}],
            meta={},
        )
        print(render_output(envelope, fmt="json", pretty=False))
        return EXIT_INTERNAL


if __name__ == "__main__":
    raise SystemExit(main())
