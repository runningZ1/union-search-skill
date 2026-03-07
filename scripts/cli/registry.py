#!/usr/bin/env python3
"""Capability registry for unified CLI."""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple
import sys


def _ensure_scripts_on_path() -> None:
    scripts_dir = Path(__file__).resolve().parents[1]
    scripts_path = str(scripts_dir)
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)


@dataclass(frozen=True)
class PlatformCapability:
    name: str
    description: str
    groups: Tuple[str, ...]
    required_env: Tuple[str, ...]
    optional_env: Tuple[str, ...]
    status: str
    notes: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


_REQUIRED_ENV: Dict[str, Tuple[str, ...]] = {
    "xiaohongshu": ("TIKHUB_TOKEN",),
    "douyin": ("TIKHUB_TOKEN",),
    "bilibili": ("TIKHUB_TOKEN",),
    "twitter": ("TIKHUB_TOKEN",),
    "weibo": ("WEIBO_COOKIE", "WEIBO_USER_ID"),
    "zhihu": ("TIKHUB_TOKEN",),
    "google": ("GOOGLE_API_KEY", "GOOGLE_SEARCH_ENGINE_ID"),
    "tavily": ("TAVILY_API_KEY",),
    "jina": ("JINA_API_KEY",),
    "yandex": ("SERPAPI_API_KEY",),
    "bing": ("SERPAPI_API_KEY",),
    "metaso": ("METASO_API_KEY",),
    "volcengine": ("VOLCENGINE_API_KEY",),
    "baidu": ("BAIDU_QIANFAN_API_KEY",),
    "youtube": ("YOUTUBE_API_KEY",),
    # Defuddle requires Node.js but no API key
}

_OPTIONAL_ENV: Dict[str, Tuple[str, ...]] = {
    "github": ("GITHUB_TOKEN",),
    "duckduckgo": ("DUCKDUCKGO_PROXY",),
    "brave": ("BRAVE_PROXY",),
    "yahoo": ("YAHOO_PROXY",),
    "wikipedia": ("WIKIPEDIA_PROXY",),
}

_STATUS: Dict[str, str] = {
    "xiaohongshu": "disabled",
    "weibo": "disabled",
    "reddit": "degraded",
    "volcengine": "degraded",
}

_NOTES: Dict[str, str] = {
    "xiaohongshu": "Temporarily disabled in union orchestrator.",
    "weibo": "Requires dedicated implementation and credentials.",
    "reddit": "May hit 403 depending on source endpoint and IP.",
    "volcengine": "Historically had response parsing instability.",
}

IMAGE_PLATFORMS: Tuple[str, ...] = (
    "baidu",
    "bing",
    "google",
    "i360",
    "pixabay",
    "yandex",
    "sogou",
    "yahoo",
    "unsplash",
    "gelbooru",
    "safebooru",
    "danbooru",
    "pexels",
    "huaban",
    "foodiesfeed",
    "volcengine",
)


def load_capabilities() -> List[PlatformCapability]:
    """Build capabilities from union search metadata."""
    _ensure_scripts_on_path()
    from union_search.union_search import PLATFORM_GROUPS, PLATFORM_MODULES

    group_lookup: Dict[str, List[str]] = {}
    for group_name, group_platforms in PLATFORM_GROUPS.items():
        for item in group_platforms:
            group_lookup.setdefault(item, []).append(group_name)

    capabilities: List[PlatformCapability] = []
    for name, meta in PLATFORM_MODULES.items():
        description = str(meta.get("description", ""))
        groups = tuple(sorted(g for g in group_lookup.get(name, []) if g != "all"))
        required_env = _REQUIRED_ENV.get(name, ())
        optional_env = _OPTIONAL_ENV.get(name, ())
        status = _STATUS.get(name, "stable")
        notes = _NOTES.get(name, "")
        capabilities.append(
            PlatformCapability(
                name=name,
                description=description,
                groups=groups,
                required_env=required_env,
                optional_env=optional_env,
                status=status,
                notes=notes,
            )
        )

    capabilities.sort(key=lambda x: x.name)
    return capabilities


def load_groups() -> Dict[str, List[str]]:
    """Load platform groups from union search metadata."""
    _ensure_scripts_on_path()
    from union_search.union_search import PLATFORM_GROUPS

    return {name: list(values) for name, values in PLATFORM_GROUPS.items()}
