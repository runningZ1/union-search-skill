#!/usr/bin/env python3
"""Output helpers for unified CLI."""

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = "1.0"


def utc_now_iso() -> str:
    """Return current timestamp in ISO format with timezone."""
    return datetime.now(timezone.utc).isoformat()


def build_envelope(
    command: str,
    query: Optional[str],
    started_at: datetime,
    success: bool,
    data: Any,
    errors: Optional[List[Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build normalized response envelope.

    顶层遵循机器契约：schema_version、ok、type、data、error、meta。
    success、command、query、timestamp、duration_ms、errors 保留，供已有调用方继续使用。
    """
    duration_ms = int((datetime.now() - started_at).total_seconds() * 1000)
    error_list = errors or []
    envelope_meta = {
        "request_id": f"req_{uuid.uuid4().hex[:12]}",
        "duration_ms": duration_ms,
    }
    envelope_meta.update(meta or {})
    envelope: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "ok": success,
        "type": "result" if success else "error",
        "success": success,
        "command": command,
        "query": query,
        "timestamp": utc_now_iso(),
        "duration_ms": duration_ms,
        "errors": error_list,
        "meta": envelope_meta,
    }
    if success:
        envelope["data"] = data
    else:
        primary = error_list[0] if error_list else {"code": "INTERNAL_ERROR", "message": "Unknown error"}
        envelope["error"] = {
            "code": primary.get("code", "INTERNAL_ERROR"),
            "message": primary.get("message", ""),
            "retryable": bool(primary.get("retryable", False)),
            "outcome": primary.get("outcome", "unknown"),
            "details": {"failures": error_list},
            "next_actions": primary.get("next_actions", []),
        }
    return envelope


def render_json(envelope: Dict[str, Any], pretty: bool = False) -> str:
    """Render envelope as JSON."""
    if pretty:
        return json.dumps(envelope, ensure_ascii=False, indent=2)
    return json.dumps(envelope, ensure_ascii=False)


def render_text(envelope: Dict[str, Any]) -> str:
    """Plain structured output preserves every returned row and field."""
    return json.dumps(envelope, ensure_ascii=False, indent=2)


def render_markdown(envelope: Dict[str, Any]) -> str:
    """Render complete data, without hidden first-N summaries."""
    lines = [f"# CLI Result: `{envelope.get('command')}`", ""]
    data = envelope.get("data")
    if envelope.get("command") == "defuddle" and isinstance(data, dict):
        if data.get("title"):
            lines.extend(["## " + data["title"], ""])
        lines.append(data.get("content") or data.get("markdown") or "")
    else:
        # JSON inside Markdown keeps platform-specific fields and every result.
        rendered = json.dumps(envelope, ensure_ascii=False, indent=2)
        fence = "`" * max(3, max((len(m.group()) + 1 for m in re.finditer(r"`+", rendered)), default=3))
        lines.extend([fence + "json", rendered, fence])
    return "\n".join(lines)


def render_output(envelope: Dict[str, Any], fmt: str = "json", pretty: bool = False) -> str:
    """Render envelope in selected format."""
    if fmt == "json":
        return render_json(envelope, pretty=pretty)
    if fmt == "markdown":
        return render_markdown(envelope)
    return render_text(envelope)
