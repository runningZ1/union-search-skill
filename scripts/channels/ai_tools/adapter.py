"""Run the bundled native backends in a bounded, isolated Python process."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

BACKENDS = {"claude_code": "claude", "codex": "codex", "grok_build": "grok"}


def _run(request, timeout):
    if sys.version_info < (3, 10):
        raise RuntimeError("AI tool search requires Python 3.10+")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    # Absolute worker path; query/schema travel via stdin, never through a shell.
    worker = Path(__file__).with_name("worker.py")
    with tempfile.TemporaryDirectory(prefix="union-ai-search-") as cwd:
        process = subprocess.Popen(
            [sys.executable, str(worker)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
            cwd=cwd, start_new_session=os.name != "nt",
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        try:
            stdout, stderr = process.communicate(json.dumps(request, ensure_ascii=False), timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               capture_output=True, timeout=10, check=False)
            else:
                os.killpg(process.pid, signal.SIGKILL)
            process.kill()
            process.communicate()
            raise TimeoutError("Native AI search timed out after %ss" % timeout) from None
    try:
        result = json.loads(stdout)
    except (ValueError, TypeError):
        raise RuntimeError("Native search worker returned invalid JSON (exit %s)" % process.returncode) from None
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Native search failed"))
    return result


def check_backend(platform, timeout=35):
    try:
        result = _run({"operation": "check", "backend": BACKENDS[platform]}, timeout)
        return {"ok": bool(result["available"]), "message": result["message"]}
    except Exception as error:
        return {"ok": False, "message": str(error)}


def search(platform, query, limit=None, timeout=180, **params):
    if platform not in BACKENDS:
        raise ValueError("Unknown native search platform")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be non-empty")
    if limit is not None:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            raise ValueError("AI search limit must be zero (unlimited) or a positive integer")
        limit = None if limit == 0 else limit
    unknown = set(params) - {"recency_days", "domains"}
    if unknown:
        raise ValueError("Unsupported AI search parameters: " + ", ".join(sorted(unknown)))
    recency = params.get("recency_days")
    if recency is not None:
        recency = int(recency)
        if recency <= 0:
            raise ValueError("recency_days must be positive")
    domains = params.get("domains")
    if isinstance(domains, str):
        domains = [part.strip() for part in domains.split(",") if part.strip()]
    if domains is not None and (not isinstance(domains, list) or not all(isinstance(d, str) and d.strip() for d in domains)):
        raise ValueError("domains must be a list or comma-separated host names")
    result = _run({"operation": "search", "backend": BACKENDS[platform], "query": query,
                   "limit": limit, "recency_days": recency, "domains": domains}, timeout)
    return [{**row, "backend": BACKENDS[platform], "untrusted": True} for row in result["results"][:limit]]
