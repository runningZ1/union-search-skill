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
if str(CURRENT_DIR.parent) not in sys.path:
    sys.path.insert(1, str(CURRENT_DIR.parent))

from adapters import run_defuddle, run_download, run_image, run_platform, run_search
from errors import ERROR_REGISTRY, EXIT_INTERNAL, EXIT_INTERRUPTED, CliError, CliUsageError
from output import SCHEMA_VERSION, build_envelope, render_output
from registry import IMAGE_PLATFORMS, load_capabilities, load_groups
from search_output import project_search, read_results, write_full_result
from validators import parse_param_pairs, resolve_limit, resolve_query, validate_platforms
from library.defaults import DEFAULT_FETCH_OPTIONS
from library.preprocessors import PREPROCESSORS

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
            "  python scripts/cli/main.py search \"服装设计 再生面料\" --group api --fetch all\n"
            "  python scripts/cli/main.py fetch --search-id <search_id> --ids 1 3\n"
            "  python scripts/cli/main.py task status <task_id>\n"
            "  python scripts/cli/main.py read --document-id <document_id> --body\n"
            "  python scripts/cli/main.py library search \"再生涤纶\" --has-body\n"
            "  python scripts/cli/main.py library backup --backup-dir D:\\backups\\library-20261106\n"
            "  python scripts/cli/main.py library export --search-id <search_id> --export-file .work/export.json\n"
        ),
    )
    parser.add_argument("--version", action="version", version=f"union-search CLI v{__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # search
    search_parser = subparsers.add_parser("search", help="Aggregated multi-platform search", parents=[common])
    search_parser.add_argument("query", nargs="?", help="Search query")
    search_parser.add_argument("--query", dest="query_opt", help="Search query (overrides positional)")
    search_parser.add_argument("--platforms", "-p", nargs="+", help="Specific platforms")
    search_parser.add_argument("--group", "-g", help="Platform group: general (default, no required API key), api, ai_tools (local accounts), dev, social, preferred, tools, all; aliases: search/no_api_key")
    search_parser.add_argument("--limit", "-l", type=int, default=None, help="Per-platform result cap (default: unlimited; 0 unlimited)")
    search_parser.add_argument("--preset", choices=["small", "medium", "large", "extra"], help="Predefined result limits (small=3, medium=5, large=10, extra=20)")
    search_parser.add_argument("--max-workers", type=int, default=None, help="Channels searched at the same time (default: all selected channels at once)")
    search_parser.add_argument("--timeout", type=int, default=60, help="Timeout seconds")
    search_parser.add_argument("--deduplicate", action=argparse.BooleanOptionalAction, default=True, help="Merge duplicates by canonical page URL (default on; use --no-deduplicate to keep duplicates)")
    search_parser.add_argument("--fail-on-platform-error", action="store_true", help="Exit non-zero on partial platform failures")
    search_parser.add_argument("--env-file", default=".env", help="Env file path")
    _add_output_args(search_parser)
    _add_search_output_args(search_parser)
    _add_fetch_args(search_parser)

    # platform
    platform_parser = subparsers.add_parser("platform", help="Run a single platform", parents=[common])
    platform_parser.add_argument("platform", help="Platform name")
    platform_parser.add_argument("query", nargs="?", help="Search query")
    platform_parser.add_argument("--query", dest="query_opt", help="Search query (overrides positional)")
    platform_parser.add_argument("--limit", "-l", type=int, default=None, help="Result cap (default: unlimited; 0 unlimited)")
    platform_parser.add_argument("--timeout", type=int, default=60, help="Timeout seconds")
    platform_parser.add_argument("--param", action="append", help="Adapter passthrough key=value (repeatable)")
    platform_parser.add_argument("--fail-on-platform-error", action="store_true", help="Exit non-zero if platform fails")
    platform_parser.add_argument("--env-file", default=".env", help="Env file path")
    _add_output_args(platform_parser)
    _add_search_output_args(platform_parser)
    _add_fetch_args(platform_parser)

    read_parser = subparsers.add_parser("read", help="Read saved search items or library documents locally, without network requests", parents=[common])
    read_parser.add_argument("--from-file", help="Search output or full archive JSON (use with --ids)")
    read_parser.add_argument("--ids", nargs="+", type=int, help="Result IDs to read from --from-file")
    read_parser.add_argument("--document-id", nargs="+", help="Library document IDs to read (use with --body and/or --summaries)")
    read_parser.add_argument("--body", action="store_true", help="Return the complete current body of each document")
    read_parser.add_argument("--summaries", action="store_true", help="Return every archived search hit with its complete summary and raw fields")
    read_parser.add_argument("--env-file", default=".env", help="Env file path")
    _add_output_args(read_parser)

    # fetch：从已归档搜索中选择资料创建抓取任务
    fetch_parser = subparsers.add_parser("fetch", help="Create a background fetch task for archived results or documents", parents=[common])
    fetch_parser.add_argument("--search-id", help="Archived search run ID")
    fetch_parser.add_argument("--ids", nargs="+", type=int, help="Result IDs within the search run")
    fetch_parser.add_argument("--all", action="store_true", help="Every unique link of the search run")
    fetch_parser.add_argument("--document-ids", nargs="+", help="Library document IDs")
    fetch_parser.add_argument("--fetch-concurrency", type=int, help=f"Parallel items (default {DEFAULT_FETCH_OPTIONS['concurrency']})")
    fetch_parser.add_argument("--fetch-per-host", type=int, help=f"Parallel items per host (default {DEFAULT_FETCH_OPTIONS['per_host']})")
    fetch_parser.add_argument("--fetch-timeout", type=int, help=f"Per-item timeout seconds (default {DEFAULT_FETCH_OPTIONS['timeout']})")
    fetch_parser.add_argument("--wait", action="store_true", help="Wait until the task ends")
    fetch_parser.add_argument("--wait-timeout", type=int, help="Max seconds to wait with --wait (default: no limit)")
    fetch_parser.add_argument("--env-file", default=".env", help="Env file path")
    _add_output_args(fetch_parser)

    # task：查看和控制抓取任务
    task_parser = subparsers.add_parser("task", help="Inspect or control fetch tasks", parents=[common])
    task_parser.add_argument("action", choices=["status", "wait", "resume", "retry", "cancel", "list"])
    task_parser.add_argument("task_id", nargs="?", help="Task ID (not used by list)")
    task_parser.add_argument("--failed", action="store_true", help="retry: put failed items back into the queue (required for retry)")
    task_parser.add_argument("--timeout", type=int, help="wait: max seconds (default: no limit)")
    task_parser.add_argument("--limit", type=int, default=20, help="list: number of recent tasks")
    task_parser.add_argument("--env-file", default=".env", help="Env file path")
    _add_output_args(task_parser)

    # library：本地资料库检索与维护
    library_parser = subparsers.add_parser("library", help="Search and maintain the long-term local library", parents=[common])
    library_parser.add_argument("action", choices=["search", "status", "reindex", "import", "repair", "backup", "restore", "export"])
    library_parser.add_argument("query", nargs="?", help="search: query text")
    library_parser.add_argument("paths", nargs="*", help="import: full.json files or directories")
    library_parser.add_argument("--has-body", action=argparse.BooleanOptionalAction, default=None, help="search: only documents with (or --no-has-body without) a body")
    library_parser.add_argument("--content-type", nargs="+", choices=["article", "listing", "video", "podcast", "pdf", "other", "unknown"])
    library_parser.add_argument("--fetch-status", nargs="+", choices=["not_fetched", "succeeded", "unchanged", "partial", "restricted", "failed", "pending_preprocess"])
    library_parser.add_argument("--platforms", nargs="+", help="search: search platforms that returned the document")
    library_parser.add_argument("--domain", nargs="+", help="search: domains")
    library_parser.add_argument("--limit", type=int, default=0, help="search: result cap (default: unlimited; 0 unlimited)")
    library_parser.add_argument("--content", choices=["full", "none"], default="full", help="search: show complete search summaries (default) or hide them")
    library_parser.add_argument("--all", action="store_true", help="reindex: rebuild the whole index from the archive")
    library_parser.add_argument("--backup-dir", help="backup: new or empty directory for the database dump, body files and manifest")
    library_parser.add_argument("--from", dest="from_dir", help="restore: backup directory; the configured database, library directory and index must be empty")
    library_parser.add_argument("--search-id", help="export: archived search run ID")
    library_parser.add_argument("--task-id", help="export: fetch task of that search (default: its latest task)")
    library_parser.add_argument("--export-file", help="export: JSON file grouped by channel, with each result's fetch outcome and body file")
    library_parser.add_argument("--env-file", default=".env", help="Env file path")
    _add_output_args(library_parser)

    # image
    image_parser = subparsers.add_parser("image", help="Multi-platform image search/download", parents=[common])
    image_parser.add_argument("query", nargs="?", help="Search query")
    image_parser.add_argument("--query", dest="query_opt", help="Search query (overrides positional)")
    image_parser.add_argument("--platforms", "-p", nargs="+", help="Image platforms")
    image_parser.add_argument("--limit", "-l", type=int, default=0, help="Images per platform (default: unlimited; 0 unlimited)")
    image_parser.add_argument("--output-dir", default="image_downloads", help="Output directory")
    image_parser.add_argument("--threads", type=int, default=5, help="Download threads")
    image_parser.add_argument("--delay", type=float, default=1.0, help="Delay between platforms in seconds")
    image_parser.add_argument("--no-metadata", action="store_true", help="Disable metadata output")
    image_parser.add_argument("--search-only", action="store_true", help="Return image URLs and metadata without downloading")
    image_parser.add_argument("--env-file", default=".env", help="Env file path")
    image_parser.add_argument("--timeout", type=int, default=1800, help="Command timeout seconds")
    _add_output_args(image_parser)

    # download
    download_parser = subparsers.add_parser("download", help="Download media using yt-dlp", parents=[common])
    download_parser.add_argument("urls", nargs="*", help="Direct media URLs to download")
    download_parser.add_argument("--from-file", help="Load URLs from search result JSON file")
    download_parser.add_argument("--platforms", "-p", nargs="+", help="Filter platforms when using --from-file")
    download_parser.add_argument("--select", help="Select candidate indices from --from-file, e.g. 1,3,5")
    download_parser.add_argument("--limit", "-l", type=int, default=None, help="Candidate cap (default: unlimited; 0 unlimited)")
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


def _add_search_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--view", choices=["compact", "full"], default="compact", help="Default compact omits duplicate per-channel rows; full restores the legacy layout")
    parser.add_argument("--content", choices=["full", "none"], default="full", help="Show complete search content (default: full) or hide it; full content is archived locally")


def _add_fetch_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--fetch", choices=["all"], help="After archiving, create a background task fetching every unique result link (default: archive only)")
    parser.add_argument("--fetch-concurrency", type=int, help=f"Parallel fetch items (default {DEFAULT_FETCH_OPTIONS['concurrency']})")
    parser.add_argument("--fetch-per-host", type=int, help=f"Parallel fetch items per host (default {DEFAULT_FETCH_OPTIONS['per_host']})")
    parser.add_argument("--fetch-timeout", type=int, help=f"Per-item fetch timeout seconds (default {DEFAULT_FETCH_OPTIONS['timeout']})")


def _add_platform_execution_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--query", dest="query_opt", help="Search query (overrides positional)")
    parser.add_argument("--limit", "-l", type=int, default=None, help="Result cap (default: unlimited; 0 unlimited)")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout seconds")
    parser.add_argument("--param", action="append", help="Adapter passthrough key=value (repeatable)")
    parser.add_argument("--fail-on-platform-error", action="store_true", help="Exit non-zero if platform fails")
    parser.add_argument("--env-file", default=".env", help="Env file path")
    _add_output_args(parser)
    _add_search_output_args(parser)
    _add_fetch_args(parser)


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
        on_channel_done=args.fetch_stream.add_channel if getattr(args, "fetch_stream", None) else None,
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
        limit=resolve_limit(args.limit, None),
        timeout=args.timeout,
        env_file=args.env_file,
        params=params,
    )
    success = bool(data.get("success"))
    errors: List[Dict[str, Any]] = []
    if not success:
        errors.append(
            {
                "code": data.get("error_details", {}).get("code", "PLATFORM_FAILURE"),
                "message": str(data.get("error") or "Platform failed"),
                "retryable": data.get("error_details", {}).get("retryable", False),
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
        limit=resolve_limit(args.limit, None) or 0,
        output_dir=args.output_dir,
        threads=args.threads,
        delay=args.delay,
        no_metadata=args.no_metadata,
        env_file=args.env_file,
        timeout=args.timeout,
        search_only=args.search_only,
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
        "meta": {"selected_image_platforms": [platform["platform"] for platform in data.get("platforms", [])]},
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
        limit=resolve_limit(args.limit, None),
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
        {"name": "read", "effect": "read", "is_idempotent": True, "description": "按 ID 读取本地搜索条目，或按资料 ID 读取正文与全部搜索命中；不发起网络请求"},
        {"name": "fetch", "effect": "write", "is_idempotent": False, "description": "为已归档搜索结果或资料创建后台抓取任务，立即返回任务 ID"},
        {"name": "task", "effect": "write", "is_idempotent": False, "description": "查看、等待、恢复、重试失败项或取消抓取任务"},
        {"name": "library", "effect": "write", "is_idempotent": False, "description": "本地资料库检索、状态、索引重建、旧归档导入、正文文件核对、备份与恢复"},
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
            "image_search": {"default_platforms": ["baidu", "bing", "wikicommons"], "search_only_option": "--search-only", "item_fields": ["id", "provider", "title", "image_url", "source_url", "thumbnail", "width", "height", "author", "license", "image_variant", "file_path", "download_status"], "image_variant": ["original", "largest_available"]},
            "limits": {"presets": {"small": 3, "medium": 5, "large": 10, "extra": 20}, "default_search_platforms": "general", "default_result_limit": None, "unlimited_value": 0, "result_scope": "all returned rows; upstream request/page limits still apply"},
            "output": {"default": "json", "formats": ["json", "markdown", "text"], "stdout": "envelope only", "stderr": "diagnostics", "output_file_json": "indented"},
            "search_output": {"default_view": "compact", "views": ["compact", "full"], "default_content": "full", "content_modes": ["full", "none"], "full_archive": ".work/search-results/<unique-id>/full.json", "read_command": "read --from-file <search.json> --ids <id> [<id> ...]", "legacy_output": "--view full --content full"},
            "library": {
                "env": ["UNION_SEARCH_LIBRARY_DIR", "UNION_SEARCH_PG_DSN", "UNION_SEARCH_ES_URL", "UNION_SEARCH_ES_API_KEY", "UNION_SEARCH_ES_INDEX"],
                "storage": {"structured": "PostgreSQL", "bodies": "<UNION_SEARCH_LIBRARY_DIR>/bodies", "search_index": "Elasticsearch <UNION_SEARCH_ES_INDEX> (rebuildable)"},
                "backup": {"command": "library backup --backup-dir <dir>", "restore": "library restore --from <dir>", "tools": ["pg_dump", "pg_restore"],
                           "contents": ["database.dump", "bodies/", "manifest.json"], "search_index": "rebuilt on restore"},
                "export": {"command": "library export --search-id <search_id> [--task-id <task_id>] --export-file <file>",
                           "format": "union-search.search-export", "grouped_by": "channel",
                           "top_level": ["format", "version", "generated_at", "search", "groups"],
                           "group_fields": ["group", "channel", "status", "result_count", "duration_ms", "error_code", "error_message", "results"],
                           "result_fields": ["index", "title", "url", "content", "published", "result_id", "document_id",
                                             "fetch_status", "fetch_reason", "body_file", "body_chars"]},
                "preprocessors": sorted(PREPROCESSORS),
                "search_archive": "search, platform and direct platform commands archive every hit into meta.library.search_id",
                "fetch_defaults": DEFAULT_FETCH_OPTIONS,
                "content_types": ["article", "listing", "video", "podcast", "pdf", "other", "unknown"],
                "restriction_kinds": ["paywall", "login", "captcha", "permission_denied", "region_blocked", "suspected", "unknown"],
                "item_statuses": ["pending", "running", "succeeded", "unchanged", "partial", "restricted", "failed", "pending_preprocess", "cancelled"],
                "task_statuses": ["queued", "running", "cancelling", "interrupted", "completed", "partial", "failed", "cancelled"],
                "change_kinds": ["first", "unchanged", "changed", "not_modified", "stale"],
            },
            "web_results": {"fields":["id", "title", "url", "content", "published", "thumbnail", "sources"], "source_fields": ["platform", "engine", "rank"], "deduplication": "canonical URL; preserve all sources", "channel_fields": ["platform", "status", "count", "duration_ms", "error"], "timing_unit": "milliseconds"},
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

    from importlib.util import find_spec
    checks: List[Dict[str, Any]] = []
    for dependency in ("curl_cffi", "lxml", "psycopg", "psycopg_pool", "elasticsearch", "bs4", "pymupdf4llm"):
        installed = find_spec(dependency) is not None
        checks.append({"name": "dependency_" + dependency, "status": "pass" if installed else "fail", "message": dependency + (" is installed" if installed else " is missing")})
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
    node_message = f"node found at {node_path}" if node_path else "Node.js not found (defuddle may fail)"
    checks.append({"name": "dependency_node", "status": node_status, "message": node_message})

    npm_path = shutil.which("npm")
    npm_status = "pass" if npm_path else "warn"
    npm_message = f"npm found at {npm_path}" if npm_path else "npm not found (cannot install Node.js dependencies)"
    checks.append({"name": "dependency_npm", "status": npm_status, "message": npm_message})

    # Check for critical npm modules if node is available
    if node_path:
        # Check root Node.js dependencies used by the content tooling.
        root_dir = Path(__file__).resolve().parents[2]
        commander_path = root_dir / "node_modules" / "commander"
        
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
        
        # 检查固定版本 npm 包的 CLI。
        defuddle_dist = root_dir / "scripts" / "url_to_markdown" / "engines" / "defuddle-node" / "node_modules" / "defuddle" / "dist" / "cli.js"
        checks.append({
            "name": "defuddle_build",
            "status": "pass" if defuddle_dist.exists() else "fail",
            "message": "Defuddle npm CLI found" if defuddle_dist.exists() else "Defuddle npm CLI missing. Run npm --prefix scripts/url_to_markdown/engines/defuddle-node ci"
        })

    checks.extend(_library_checks())

    platform_checks: List[Dict[str, Any]] = []
    for cap in capabilities:
        if selected and cap.name not in selected:
            continue
        missing = [key for key in cap.required_env if not os.getenv(key)]
        if cap.name in ("bing", "yandex") and any(
            value for key, value in os.environ.items() if key.startswith("SERPAPI_API_KEY")
        ):
            missing = [key for key in missing if key != "SERPAPI_API_KEY"]
        if cap.auth_mode == "local_account":
            from ai_tools.adapter import check_backend
            detected = check_backend(cap.name)
            status = "pass" if detected["ok"] else "warn"
            message = detected["message"]
        elif cap.status == "disabled":
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
                "auth_mode": cap.auth_mode,
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


def _library_checks() -> List[Dict[str, Any]]:
    """长期资料库的目录、PostgreSQL 与 Elasticsearch 检查；未配置时给出警告。"""
    from library.config import LibraryNotConfigured, load_config, missing_env

    try:
        config = load_config()
    except LibraryNotConfigured as exc:
        return [{"name": "library_config", "status": "warn", "message": f"{exc}; search results are not archived (missing: {', '.join(missing_env())})"}]
    checks = [{"name": "library_dir", "status": "pass", "message": f"library directory {config.root}"}]
    from library import index
    from library.db import open_library

    try:
        conn = open_library(config)
        conn.close()
        checks.append({"name": "library_postgres", "status": "pass", "message": f"PostgreSQL reachable at {config.public()['pg']}, schema ready"})
    except Exception as exc:  # doctor 如实报告连接失败
        checks.append({"name": "library_postgres", "status": "fail", "message": f"PostgreSQL unavailable: {type(exc).__name__}: {exc}"})
    try:
        es = index.client(config)
        version = es.info()["version"]["number"]
        exists = bool(es.indices.exists(index=config.es_index))
        checks.append({"name": "library_elasticsearch", "status": "pass", "message": f"Elasticsearch {version} reachable, index {config.es_index} {'exists' if exists else 'will be created on first archive'}"})
    except Exception as exc:  # doctor 如实报告连接失败
        checks.append({"name": "library_elasticsearch", "status": "fail", "message": f"Elasticsearch unavailable: {type(exc).__name__}: {exc}"})
    from library.backup import pg_tool_status

    tools = pg_tool_status()
    missing_tools = [name for name, path in tools.items() if path is None]
    checks.append({"name": "library_backup_tools", "status": "warn" if missing_tools else "pass",
                   "message": (f"{', '.join(missing_tools)} not on PATH; library backup/restore unavailable" if missing_tools
                               else "pg_dump and pg_restore found: " + ", ".join(tools.values()))})
    return checks


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


def handle_read(args: argparse.Namespace) -> Dict[str, Any]:
    if args.document_id:
        if args.from_file or args.ids:
            raise CliUsageError("--document-id 不能与 --from-file/--ids 同时使用")
        from library_commands import handle_read_documents

        return handle_read_documents(args)
    if not (args.from_file and args.ids):
        raise CliUsageError("使用 --from-file <file> --ids <id> 读取搜索条目，或使用 --document-id <id> --body 读取资料")
    if args.body or args.summaries:
        raise CliUsageError("--body/--summaries 只用于 --document-id")
    return read_results(args.from_file, args.ids)


def dispatch(args: argparse.Namespace) -> Dict[str, Any]:
    if args.command == "read":
        return handle_read(args)
    if args.command in ("fetch", "task", "library"):
        import library_commands

        if args.command == "fetch":
            return library_commands.handle_fetch(args)
        if args.command == "task":
            if args.action == "retry" and not args.failed:
                raise CliUsageError("task retry 需要 --failed，只重新处理失败项")
            return library_commands.handle_task(args)
        if args.action == "import":
            args.paths = ([args.query] if args.query else []) + list(args.paths)
            if not args.paths:
                raise CliUsageError("library import 需要至少一个文件或目录")
        return library_commands.handle_library(args)
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
        if hasattr(args, "view"):
            from library import index

            # 归档后写入检索索引要用 elasticsearch，搜索进行期间在后台导入
            index.preload()
        if hasattr(args, "view") and getattr(args, "fetch", None) == "all":
            from library_commands import open_fetch_stream

            # 搜索开始前创建抓取任务并启动执行器，每个渠道返回后立即开始抓取它的结果
            args.fetch_stream = open_fetch_stream(args)
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
        exit_code = int(result.get("runtime_exit_code", 0))
        if hasattr(args, "view"):
            from library_commands import archive_search

            write_full_result(envelope)
            exit_code = archive_search(envelope, args) or exit_code
            envelope = project_search(envelope, args.view, args.content)
        # 写入文件的 JSON 始终缩进，便于逐项查看；标准输出默认单行
        rendered = render_output(envelope, fmt=args.format, pretty=bool(args.pretty or args.output))
        write_output(rendered, args.output)
        return exit_code
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
    finally:
        # 正常归档后 finish 已结束收集，abort 不做任何事；搜索或归档中途失败时取消提前开始的抓取任务，已取得的正文保留
        stream = getattr(args, "fetch_stream", None)
        if stream is not None:
            stream.abort()
            stream.conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
