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
    requires_api_key: bool
    kind: str
    auth_mode: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


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

    from union_search.platform_metadata import REQUIRED_ENV, OPTIONAL_ENV, STATUS, NOTES, LOCAL_ACCOUNT_PLATFORMS

    capabilities: List[PlatformCapability] = []
    for name, meta in PLATFORM_MODULES.items():
        description = str(meta.get("description", ""))
        groups = tuple(sorted(g for g in group_lookup.get(name, []) if g != "all"))
        required_env = REQUIRED_ENV.get(name, ())
        optional_env = OPTIONAL_ENV.get(name, ())
        status = STATUS.get(name, "stable")
        notes = NOTES.get(name, "")
        capabilities.append(
            PlatformCapability(
                name=name,
                description=description,
                groups=groups,
                required_env=required_env,
                optional_env=optional_env,
                status=status,
                notes=notes,
                requires_api_key=bool(required_env),
                kind="tool" if name in PLATFORM_GROUPS["tools"] else "search",
                auth_mode="local_account" if name in LOCAL_ACCOUNT_PLATFORMS else ("api_key" if required_env else "anonymous"),
            )
        )

    capabilities.sort(key=lambda x: x.name)
    return capabilities


def load_groups() -> Dict[str, List[str]]:
    """Load platform groups from union search metadata."""
    _ensure_scripts_on_path()
    from union_search.union_search import PLATFORM_GROUPS

    return {name: list(values) for name, values in PLATFORM_GROUPS.items()}
