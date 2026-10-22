import os
from pathlib import Path

DEFAULT_ORDER = ("claude", "codex", "grok", "ddg")
CAPABILITIES = {
    "claude": ("search", "fetch", "research"),
    "codex": ("search", "fetch", "research"),
    "grok": ("search", "fetch", "research"),
    "ddg": ("search", "fetch", "research"),
}
DETECT_TTL_SECONDS = 300
DEFAULT_LIMIT = None
DEFAULT_MAX_CHARS = 12_000
CODEX_SEARCH_URL = "https://chatgpt.com/backend-api/codex/alpha/search"
CODEX_REFRESH_URL = "https://chatgpt.com/backend-api/auth/refresh"


def home_dir() -> Path:
    return Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())


def codex_auth_path() -> Path:
    override = os.environ.get("CODEX_AUTH_FILE")
    if override:
        return Path(override)
    return home_dir() / ".codex" / "auth.json"


def order_from_env() -> list[str]:
    raw = os.environ.get("UNIFIED_SEARCH_ORDER")
    if not raw:
        return list(DEFAULT_ORDER)
    picked = [item.strip() for item in raw.split(",") if item.strip() in DEFAULT_ORDER]
    if not picked:
        raise ValueError(f"UNIFIED_SEARCH_ORDER 没有合法后端: {raw}")
    return picked
