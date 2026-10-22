import json
import os
import shutil
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from ai_tools.native_search.config import CODEX_REFRESH_URL, CODEX_SEARCH_URL, codex_auth_path
from ai_tools.native_search.errors import BackendError, http_failure
from ai_tools.native_search.textutil import clip, dedupe_hits, hostname_of, strip_tags

UA = "codex-cli/0.163.0"


def _read_auth() -> dict:
    return json.loads(codex_auth_path().read_text(encoding="utf-8"))


def _tokens(auth: dict) -> dict:
    tokens = auth.get("tokens") or {}
    if not tokens.get("access_token"):
        raise BackendError("codex", "Codex 未登录：缺少 access_token", 401, False)
    return tokens


def detect() -> dict:
    try:
        tokens = _tokens(_read_auth())
    except (OSError, json.JSONDecodeError, BackendError) as error:
        return {"ok": False, "reason": str(error)}
    return {"ok": True, "account": tokens.get("account_id", "")}


def _refresh(tokens: dict) -> None:
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise BackendError("codex", "Codex access_token 失效且没有 refresh_token", 401, False)
    url = os.environ.get("CODEX_REFRESH_ENDPOINT") or CODEX_REFRESH_URL
    body = json.dumps({"refresh_token": refresh_token}).encode()
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": UA}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:300]
        raise http_failure("codex", error.code, f"Codex 续期失败 {error.code}: {detail}") from error
    access_token = payload.get("access_token")
    if not access_token:
        raise BackendError("codex", "Codex 续期响应没有 access_token", 401, False)
    path = codex_auth_path()
    auth = _read_auth()
    shutil.copyfile(path, Path(str(path) + ".bak"))
    auth["tokens"] = {
        **(auth.get("tokens") or {}),
        "access_token": access_token,
        "refresh_token": payload.get("refresh_token") or refresh_token,
    }
    path.write_text(json.dumps(auth, indent=2), encoding="utf-8")


def _post(tokens: dict, payload: dict, allow_refresh: bool) -> dict:
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Content-Type": "application/json",
        "User-Agent": UA,
        "originator": "codex_cli_rs",
    }
    if tokens.get("account_id"):
        headers["ChatGPT-Account-ID"] = tokens["account_id"]
    url = os.environ.get("CODEX_ENDPOINT") or CODEX_SEARCH_URL
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode(errors="replace")
        if error.code == 401 and allow_refresh:
            _refresh(tokens)
            return _post(_tokens(_read_auth()), payload, False)
        message = raw[:300]
        try:
            message = json.loads(raw).get("error", {}).get("message") or message
        except json.JSONDecodeError:
            pass
        raise http_failure("codex", error.code, message) from error


def _body(commands: dict, max_output_tokens: int | None = None) -> dict:
    body: dict = {"id": str(uuid.uuid4()), "model": "gpt-5", "commands": commands}
    if max_output_tokens:
        body["max_output_tokens"] = max_output_tokens
    return body


def _string_field(row: dict, keys: list[str]) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _hits(body: dict, limit: int | None) -> list[dict]:
    parsed: list[dict] = []
    for row in body.get("results") or []:
        if not isinstance(row, dict):
            continue
        url = _string_field(row, ["url", "link", "href"])
        title = _string_field(row, ["title", "name"]) or hostname_of(url)
        snippet = _string_field(row, ["snippet", "text", "content", "description"])
        if url or snippet:
            hit = {"title": title, "url": url, "snippet": snippet}
            ref = _string_field(row, ["ref_id", "ref"])
            if ref:
                hit["ref_id"] = ref
            parsed.append(hit)
    if not parsed:
        import re

        for title, url in re.findall(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", body.get("output") or ""):
            parsed.append({"title": title, "url": url, "snippet": ""})
    return dedupe_hits(parsed)[:limit]


def search(query: str, recency_days: int | None = None, limit: int | None = None, domains: list[str] | None = None) -> dict:
    item: dict = {"q": query}
    if recency_days:
        item["recency"] = recency_days
    if domains:
        item["domains"] = domains
    body = _post(_tokens(_read_auth()), _body({"search_query": [item]}), True)
    return {"results": _hits(body, limit), "backend": "codex", "untrusted": True}


def fetch(url: str, max_chars: int) -> dict:
    body = _post(_tokens(_read_auth()), _body({"open": [{"ref_id": url}]}, max(1, max_chars // 2)), True)
    text, truncated = clip(body.get("output") or "", max_chars)
    return {"title": hostname_of(url), "url": url, "markdown": text, "truncated": truncated, "backend": "codex", "untrusted": True}


def research(query: str, recency_days: int | None = None, limit: int | None = None) -> dict:
    item: dict = {"q": query}
    if recency_days:
        item["recency"] = recency_days
    body = _post(_tokens(_read_auth()), _body({"search_query": [item], "response_length": "medium"}, 4000), True)
    brief, _ = clip(strip_tags(body.get("output") or ""), 8000)
    return {"brief": brief, "sources": _hits(body, limit), "backend": "codex", "untrusted": True}
