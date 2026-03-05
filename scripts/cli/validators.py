#!/usr/bin/env python3
"""Validation and argument normalization helpers."""

from typing import Any, Dict, Iterable, List, Optional

from errors import CliUsageError


def resolve_query(query_positional: Optional[str], query_option: Optional[str]) -> str:
    """Resolve query from positional and optional inputs."""
    query = (query_option or query_positional or "").strip()
    if not query:
        raise CliUsageError("Missing query. Use positional query or --query.")
    return query


def validate_platforms(platforms: Iterable[str], known_platforms: Iterable[str]) -> List[str]:
    """Validate platform list and return normalized list."""
    known = set(known_platforms)
    normalized = []
    invalid = []
    for item in platforms:
        value = item.strip()
        if not value:
            continue
        if value not in known:
            invalid.append(value)
            continue
        normalized.append(value)

    if invalid:
        raise CliUsageError(f"Unknown platforms: {', '.join(invalid)}")
    return normalized


def parse_param_pairs(param_pairs: Optional[List[str]]) -> Dict[str, Any]:
    """Parse --param key=value pairs into dict."""
    data: Dict[str, Any] = {}
    for pair in param_pairs or []:
        if "=" not in pair:
            raise CliUsageError(f"Invalid --param value '{pair}', expected key=value")
        key, value = pair.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise CliUsageError(f"Invalid --param key in '{pair}'")
        data[key] = _coerce_scalar(value)
    return data


def _coerce_scalar(value: str) -> Any:
    """Best-effort scalar conversion for passthrough params."""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"none", "null"}:
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value
