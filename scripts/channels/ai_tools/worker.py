"""Private JSON stdin/stdout bridge to the bundled code; no source-repo imports."""

import importlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def execute(request):
    backend = request.get("backend")
    if backend not in {"claude", "codex", "grok"}:
        raise ValueError("Unsupported backend")
    module = importlib.import_module("ai_tools.native_search.backends." + backend)
    if request.get("operation") == "check":
        detected = module.detect()
        available = bool(detected.get("ok"))
        return {"ok": True, "available": available,
                "message": "Local authentication detected; quota and remote search not verified" if available else "Local CLI/login unavailable; install and log in to " + backend}
    if request.get("operation") != "search":
        raise ValueError("Unsupported operation")
    result = module.search(request["query"], request.get("recency_days"), request["limit"], request.get("domains"))
    if result.get("backend") != backend or result.get("fallback_from"):
        raise RuntimeError("Native backend mismatch")
    rows = result.get("results")
    if not isinstance(rows, list):
        raise ValueError("Invalid native search result")
    from urllib.parse import urlparse
    for row in rows:
        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) for k in ("url", "title", "snippet")):
            raise ValueError("Invalid native search hit")
        if urlparse(row["url"]).scheme not in {"http", "https"} or not urlparse(row["url"]).hostname:
            raise ValueError("Invalid search URL")
    return {"ok": True, "backend": backend, "results": rows, "untrusted": True}


if __name__ == "__main__":
    try:
        response = execute(json.load(sys.stdin))
    except Exception as error:
        # Never emit upstream CLI output, auth response bodies or credential values.
        response = {"ok": False, "error": "Native search failed (%s, status=%s); check local CLI/login and quota" % (type(error).__name__, getattr(error, "status", "unknown"))}
    print(json.dumps(response, ensure_ascii=False))
    sys.exit(0 if response["ok"] else 1)
