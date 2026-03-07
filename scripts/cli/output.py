#!/usr/bin/env python3
"""Output helpers for unified CLI."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    """Return current timestamp in ISO format."""
    return datetime.now().isoformat()


def build_envelope(
    command: str,
    query: Optional[str],
    started_at: datetime,
    success: bool,
    data: Any,
    errors: Optional[List[Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build normalized response envelope."""
    duration_ms = int((datetime.now() - started_at).total_seconds() * 1000)
    return {
        "success": success,
        "command": command,
        "query": query,
        "timestamp": utc_now_iso(),
        "duration_ms": duration_ms,
        "data": data,
        "errors": errors or [],
        "meta": meta or {},
    }


def render_json(envelope: Dict[str, Any], pretty: bool = False) -> str:
    """Render envelope as JSON."""
    if pretty:
        return json.dumps(envelope, ensure_ascii=False, indent=2)
    return json.dumps(envelope, ensure_ascii=False)


def render_text(envelope: Dict[str, Any]) -> str:
    """Render concise text output."""
    lines = [
        f"success: {envelope.get('success')}",
        f"command: {envelope.get('command')}",
        f"query: {envelope.get('query')}",
        f"duration_ms: {envelope.get('duration_ms')}",
        f"errors: {len(envelope.get('errors', []))}",
    ]
    return "\n".join(lines)


def render_markdown(envelope: Dict[str, Any]) -> str:
    """Render concise markdown output with key data."""
    lines = [
        f"# CLI Result: `{envelope.get('command')}`",
        "",
        f"- **success**: {envelope.get('success')}",
        f"- **query**: {envelope.get('query')}",
        f"- **duration_ms**: {envelope.get('duration_ms')}",
        f"- **errors**: {len(envelope.get('errors', []))}",
    ]

    # Defuddle special handling - show extracted content
    if envelope.get("command") == "defuddle":
        data = envelope.get("data", {})
        if data:
            lines.append("")
            lines.append("---")
            lines.append("")
            # Show title if available
            title = data.get("title", "")
            if title:
                lines.append(f"## {title}")
                lines.append("")
            # Show content
            content = data.get("content", "") or data.get("markdown", "")
            if content:
                lines.append(content)
            # Show metadata if JSON output
            if data.get("author"):
                lines.append("")
                lines.append(f"*Author: {data['author']}*")
            if data.get("published"):
                lines.append(f"*Published: {data['published']}*")
            if data.get("description"):
                lines.append("")
                lines.append(f"*Description: {data['description']}*")

    # Include key data summary for other commands if available
    data = envelope.get("data")
    if data and envelope.get("command") != "defuddle":
        # Platform list
        if "platforms" in data and isinstance(data["platforms"], list):
            lines.append("")
            lines.append("## Platforms")
            for p in data["platforms"][:10]:  # Show first 10
                if isinstance(p, dict):
                    name = p.get("name", "")
                    desc = p.get("description", "")
                    status = p.get("status", "")
                    lines.append(f"- **{name}** ({status}): {desc}")
                else:
                    # Handle string platform names (e.g., from search results)
                    lines.append(f"- {p}")
            if len(data["platforms"]) > 10:
                lines.append(f"- ... and {len(data['platforms']) - 10} more")

        # Groups
        if "groups" in data and isinstance(data["groups"], dict):
            lines.append("")
            lines.append("## Groups")
            for gname, gmembers in list(data["groups"].items())[:5]:
                lines.append(f"- **{gname}**: {', '.join(gmembers[:5])}{'...' if len(gmembers) > 5 else ''}")

        # Image platforms
        if "image_platforms" in data and isinstance(data["image_platforms"], list):
            lines.append("")
            lines.append("## Image Platforms")
            lines.append(", ".join(data["image_platforms"][:10]))
            if len(data["image_platforms"]) > 10:
                lines.append(f"... and {len(data['image_platforms']) - 10} more")

        # Search results summary
        if "results" in data and isinstance(data["results"], dict):
            lines.append("")
            lines.append("## Search Results")
            for plat, res in list(data["results"].items())[:5]:
                items = res.get("items", [])
                success = res.get("success", False)
                lines.append(f"- **{plat}**: {'✓' if success else '✗'} ({len(items)} items)")

        # Download candidates summary
        if "download_candidates" in data and isinstance(data["download_candidates"], list):
            lines.append("")
            lines.append("## Download Candidates")
            for item in data["download_candidates"][:10]:
                index = item.get("index", "")
                platform = item.get("platform", "")
                title = item.get("title", "")
                lines.append(f"- **[{index}] {platform}**: {title}")
            if len(data["download_candidates"]) > 10:
                lines.append(f"- ... and {len(data['download_candidates']) - 10} more")

        # Doctor checks summary
        if "checks" in data and isinstance(data["checks"], list):
            lines.append("")
            lines.append("## Health Checks")
            passed = sum(1 for c in data["checks"] if c.get("status") == "pass")
            failed = sum(1 for c in data["checks"] if c.get("status") == "fail")
            warn = sum(1 for c in data["checks"] if c.get("status") == "warn")
            lines.append(f"- Passed: {passed}, Failed: {failed}, Warnings: {warn}")
            # Show first 5 checks
            for c in data["checks"][:5]:
                name = c.get("name", "")
                status = c.get("status", "")
                msg = c.get("message", "")
                icon = "✓" if status == "pass" else "✗" if status == "fail" else "⚠"
                lines.append(f"  - {icon} **{name}**: {msg}")

        # Platform status in doctor (platform_checks)
        if (
            "platforms" in data
            and isinstance(data["platforms"], list)
            and "summary" in data
            and data["platforms"]
            and isinstance(data["platforms"][0], dict)
            and "platform" in data["platforms"][0]
        ):
            # This is doctor platform status.
            lines.append("")
            lines.append("## Platform Status")
            for p in data["platforms"][:10]:
                platform = p.get("platform", "")
                status = p.get("status", "")
                msg = p.get("message", "")
                icon = "✓" if status == "pass" else "✗" if status == "fail" else "⚠"
                lines.append(f"- {icon} **{platform}**: {msg}")

        # Summary section
        if "summary" in data and isinstance(data["summary"], dict):
            lines.append("")
            lines.append("## Summary")
            for k, v in data["summary"].items():
                lines.append(f"- **{k}**: {v}")

    # Errors
    errors = envelope.get("errors", [])
    if errors:
        lines.append("")
        lines.append("## Errors")
        for err in errors:
            code = err.get("code", "unknown")
            msg = err.get("message", "")
            lines.append(f"- **{code}**: {msg}")

    return "\n".join(lines)


def render_output(envelope: Dict[str, Any], fmt: str = "json", pretty: bool = False) -> str:
    """Render envelope in selected format."""
    if fmt == "json":
        return render_json(envelope, pretty=pretty)
    if fmt == "markdown":
        return render_markdown(envelope)
    return render_text(envelope)
