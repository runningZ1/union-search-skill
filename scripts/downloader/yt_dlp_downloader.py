#!/usr/bin/env python3
"""yt-dlp based downloader utilities for unified CLI."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


_URL_KEYS: Tuple[str, ...] = ("url", "href", "link", "permalink", "source_url", "arcurl")
_YOUTUBE_HOST_MARKERS: Tuple[str, ...] = ("youtube.com", "youtu.be")


def load_env_file(path: str) -> None:
    """Load env vars from file if key is not already present."""
    if not path or not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value


def _extract_url_from_item(item: Dict[str, Any], platform: str) -> str:
    for key in _URL_KEYS:
        value = item.get(key)
        if value:
            return str(value).strip()

    # Platform-specific fallback URL construction.
    if platform == "youtube":
        video_id = item.get("video_id")
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"

    if platform == "bilibili":
        bvid = item.get("bvid")
        if bvid:
            return f"https://www.bilibili.com/video/{bvid}"

    if platform == "douyin":
        aweme_id = (
            (item.get("video_info") or {}).get("aweme_id")
            if isinstance(item.get("video_info"), dict)
            else item.get("aweme_id")
        )
        if aweme_id:
            return f"https://www.douyin.com/video/{aweme_id}"

    return ""


def _extract_title(item: Dict[str, Any]) -> str:
    candidates = [
        item.get("title"),
        item.get("name"),
        item.get("desc"),
        (item.get("video_info") or {}).get("title") if isinstance(item.get("video_info"), dict) else None,
    ]
    for value in candidates:
        if value:
            return str(value).strip()
    return ""


def _parse_selection_indices(raw: Optional[str]) -> Optional[set]:
    if not raw:
        return None

    values = set()
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if not re.match(r"^\d+$", token):
            raise ValueError(f"Invalid --select token '{token}', expected positive integers like 1,2,3")
        idx = int(token)
        if idx <= 0:
            raise ValueError("--select indices must be >= 1")
        values.add(idx)
    return values


def _iter_search_items(payload: Dict[str, Any]) -> Iterable[Tuple[str, Dict[str, Any]]]:
    # Envelope shape: { data: { results: { platform: { items: [...] } }, final_items: [...] } }
    container = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(container, dict):
        return

    results = container.get("results")
    if isinstance(results, dict):
        for platform, platform_result in results.items():
            items = platform_result.get("items", []) if isinstance(platform_result, dict) else []
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict):
                    yield str(platform), item

    final_items = container.get("final_items")
    if isinstance(final_items, list):
        for item in final_items:
            if not isinstance(item, dict):
                continue
            platform = str(item.get("platform") or "unknown")
            data = item.get("data") if isinstance(item.get("data"), dict) else item
            if isinstance(data, dict):
                yield platform, data


def _select_and_limit_candidates(
    candidates: List[Dict[str, Any]],
    select: Optional[str],
    limit: Optional[int],
) -> List[Dict[str, Any]]:
    selection = _parse_selection_indices(select)
    filtered = candidates
    if selection is not None:
        filtered = [c for c in filtered if c.get("index") in selection]
    if limit is not None and limit > 0:
        filtered = filtered[:limit]
    return filtered


def _normalize_download_candidates(
    candidates: List[Dict[str, Any]],
    platforms: Optional[Sequence[str]] = None,
    select: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    allowed = set(platforms or [])
    normalized: List[Dict[str, Any]] = []
    seen_urls = set()

    for item in candidates:
        if not isinstance(item, dict):
            continue
        platform = str(item.get("platform") or "unknown")
        if allowed and platform not in allowed:
            continue

        url = str(item.get("url") or "").strip()
        if not url or url in seen_urls:
            continue

        seen_urls.add(url)
        normalized.append(
            {
                "index": len(normalized) + 1,
                "platform": platform,
                "title": str(item.get("title") or "").strip(),
                "url": url,
            }
        )

    return _select_and_limit_candidates(normalized, select=select, limit=limit)


def build_download_candidates(
    payload: Dict[str, Any],
    platforms: Optional[Sequence[str]] = None,
    select: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Build stable downloadable candidates from search payload."""
    container = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(container, dict):
        return []

    existing = container.get("download_candidates")
    if isinstance(existing, list):
        return _normalize_download_candidates(existing, platforms=platforms, select=select, limit=limit)

    generated: List[Dict[str, Any]] = []
    allowed = set(platforms or [])
    seen_urls = set()
    for platform, item in _iter_search_items(payload):
        if allowed and platform not in allowed:
            continue
        url = _extract_url_from_item(item, platform)
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        generated.append(
            {
                "index": len(generated) + 1,
                "platform": platform,
                "title": _extract_title(item),
                "url": url,
            }
        )

    return _select_and_limit_candidates(generated, select=select, limit=limit)


def collect_urls_from_search_output(
    from_file: str,
    platforms: Optional[Sequence[str]] = None,
    select: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    path = Path(from_file)
    if not path.exists():
        raise FileNotFoundError(f"Search result file not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    return build_download_candidates(raw, platforms=platforms, select=select, limit=limit)


def _build_ytdlp_command(
    urls: List[str],
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
    dry_run: bool,
) -> List[str]:
    if shutil.which("yt-dlp") is None:
        raise RuntimeError("yt-dlp is not installed or not in PATH")

    cmd: List[str] = ["yt-dlp", "--no-playlist", "--newline", "-P", output_dir, "-o", "%(uploader)s/%(title)s [%(id)s].%(ext)s"]

    if cookies_file:
        cmd.extend(["--cookies", cookies_file])
    if audio_only:
        cmd.extend(["-x", "--audio-format", audio_format or "mp3"])
    if media_format:
        cmd.extend(["-f", media_format])
    if max_height and max_height > 0:
        cmd.extend(["-S", f"res:{max_height}"])
    if cookies_from_browser:
        cmd.extend(["--cookies-from-browser", cookies_from_browser])
    if restrict_filenames:
        cmd.append("--restrict-filenames")
    if continue_download:
        cmd.append("--continue")
    if retries is not None and retries >= 0:
        cmd.extend(["--retries", str(retries)])
    if fragment_retries is not None and fragment_retries >= 0:
        cmd.extend(["--fragment-retries", str(fragment_retries)])
    if retry_sleep:
        cmd.extend(["--retry-sleep", retry_sleep])
    if proxy:
        cmd.extend(["--proxy", proxy])
    if dry_run:
        cmd.extend(["--simulate", "--skip-download"])

    cmd.extend(urls)
    return cmd


def _is_youtube_url(url: str) -> bool:
    lowered = url.lower()
    return any(marker in lowered for marker in _YOUTUBE_HOST_MARKERS)


def _candidate_cookie_files() -> List[str]:
    env_value = (os.getenv("YTDLP_COOKIES_FILE") or "").strip()
    candidates = []
    if env_value:
        candidates.append(env_value)
    candidates.extend(
        [
            str(Path.home() / ".claude" / "skills" / "yt-dlp-skill" / "cookies" / "cookies.txt"),
            str(Path.home() / ".agents" / "skills" / "yt-dlp-skill" / "cookies" / "cookies.txt"),
        ]
    )
    return candidates


def _resolve_cookie_file(explicit_cookie_file: Optional[str], urls: List[str]) -> Optional[str]:
    if explicit_cookie_file:
        p = Path(explicit_cookie_file)
        return str(p) if p.exists() else None

    if not any(_is_youtube_url(url) for url in urls):
        return None

    for candidate in _candidate_cookie_files():
        if candidate and Path(candidate).exists():
            return candidate
    return None


def run_yt_dlp_download(
    urls: List[str],
    output_dir: str,
    audio_only: bool = False,
    audio_format: str = "mp3",
    media_format: Optional[str] = None,
    max_height: Optional[int] = None,
    cookies_file: Optional[str] = None,
    cookies_from_browser: Optional[str] = None,
    restrict_filenames: bool = True,
    continue_download: bool = True,
    retries: Optional[int] = None,
    fragment_retries: Optional[int] = None,
    retry_sleep: Optional[str] = None,
    proxy: Optional[str] = None,
    timeout: int = 3600,
    dry_run: bool = False,
) -> Dict[str, Any]:
    if not urls:
        raise ValueError("No downloadable URLs found")

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    resolved_cookie_file = _resolve_cookie_file(cookies_file, urls)

    cmd = _build_ytdlp_command(
        urls=urls,
        output_dir=str(target_dir),
        audio_only=audio_only,
        audio_format=audio_format,
        media_format=media_format,
        max_height=max_height,
        cookies_file=resolved_cookie_file,
        cookies_from_browser=cookies_from_browser,
        restrict_filenames=restrict_filenames,
        continue_download=continue_download,
        retries=retries,
        fragment_retries=fragment_retries,
        retry_sleep=retry_sleep,
        proxy=proxy,
        dry_run=dry_run,
    )

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    success = proc.returncode == 0

    return {
        "success": success,
        "exit_code": proc.returncode,
        "command": cmd,
        "output_dir": str(target_dir),
        "download_count": len(urls),
        "cookies_file_used": resolved_cookie_file,
        "stdout": (proc.stdout or "").strip(),
        "stderr": (proc.stderr or "").strip(),
    }
