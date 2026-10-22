import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from ai_tools.native_search.config import home_dir
from ai_tools.native_search.errors import BackendError
from ai_tools.native_search.textutil import clip, dedupe_hits, hostname_of

SEARCH_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["results"],
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "url", "snippet"],
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "snippet": {"type": "string"},
                    "published_at": {"type": "string"},
                },
            },
        }
    },
}

FETCH_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "url", "markdown"],
    "properties": {"title": {"type": "string"}, "url": {"type": "string"}, "markdown": {"type": "string"}},
}


def which(binary: str) -> str:
    found = shutil.which(binary)
    if not found:
        raise BackendError(binary, f"找不到 {binary}", 500, False)
    # npm's Windows CMD shim re-parses quotes/newlines in prompt and schema.
    # Prefer the native Claude executable it wraps; never send prompts via cmd.exe.
    path = Path(found)
    if os.name == "nt" and path.suffix.lower() in (".cmd", ".bat"):
        native = path.parent / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
        if path.stem.lower() == "claude" and native.is_file():
            return str(native)
        raise BackendError(binary, f"请将 CLI_BIN 指向原生可执行文件，不能使用 CMD 包装脚本: {found}", 500, False)
    return found


def _diagnostic(backend: str, stdout: str, stderr: str, returncode: int | None) -> None:
    directory = os.environ.get("UNIFIED_SEARCH_DEBUG_DIR")
    if directory:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        (path / f"{backend}-{uuid.uuid4().hex}.json").write_text(
            json.dumps({"backend": backend, "returncode": returncode, "stdout": stdout,
                        "stderr": stderr}, ensure_ascii=False, indent=2), encoding="utf-8")


def run(binary: str, args: list[str], timeout: int, backend: str, env: dict | None = None) -> str:
    try:
        completed = subprocess.run(
            [which(binary), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as error:
        raise BackendError(backend, f"{binary} 超时 {timeout}s", 504, True) from error
    _diagnostic(backend, completed.stdout, completed.stderr, completed.returncode)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or f"退出码 {completed.returncode}").strip()
        raise BackendError(backend, detail[:500], 500, True)
    return completed.stdout.strip()


def _objects(raw: str):
    decoder = json.JSONDecoder()
    offset = 0
    while (start := raw.find("{", offset)) >= 0:
        try:
            value, end = decoder.raw_decode(raw, start)
        except json.JSONDecodeError:
            offset = start + 1
            continue
        offset = end
        if isinstance(value, dict):
            yield value


def _valid(value: dict, kind: str | None) -> bool:
    if kind in (None, "search") and isinstance(value.get("results"), list):
        return all(isinstance(row, dict) and all(isinstance(row.get(k), str)
                   for k in ("title", "url", "snippet")) for row in value["results"])
    return kind in (None, "fetch") and all(isinstance(value.get(k), str)
                                          for k in ("title", "url", "markdown"))


def parse_object(raw: str, backend: str, kind: str | None = None) -> dict:
    candidates = []
    for parsed in _objects(raw):
        if parsed.get("is_error"):
            raise BackendError(backend, f"{backend} CLI 执行失败: {parsed.get('result', '')[:240]}", 502, True)
        structured = parsed.get("structured_output") or parsed.get("structuredOutput")
        if isinstance(structured, dict) and _valid(structured, kind):
            candidates.append(structured)
            continue
        if _valid(parsed, kind):
            candidates.append(parsed)
        for key in ("result", "text"):
            if isinstance(parsed.get(key), str):
                candidates.extend(value for value in _objects(parsed[key]) if _valid(value, kind))
    if candidates:
        return candidates[-1]
    raise BackendError(backend, f"{backend} 没有合法结构化结果: {raw[:240]}", 502, True)


def require_tool_call(raw: str, backend: str, names: set[str]) -> None:
    """A model-generated list of links alone is not native-search evidence."""
    def contains(value):
        if isinstance(value, dict):
            if value.get("type") in {"tool_use", "server_tool_use"} and value.get("name") in names:
                return True
            return any(contains(child) for child in value.values())
        return isinstance(value, list) and any(contains(child) for child in value)
    if not any(contains(event) for event in _objects(raw)):
        raise BackendError(backend, "No native tool invocation in CLI stream", 502, True)


def grok_logged_in() -> bool:
    return (home_dir() / ".grok" / "auth.json").is_file()


def claude_logged_in() -> bool:
    try:
        binary = which(os.environ.get("CLAUDE_BIN") or "claude")
    except BackendError:
        return False
    completed = subprocess.run([binary, "auth", "status"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, check=False)
    if completed.returncode != 0:
        return False
    try:
        return json.loads(completed.stdout).get("loggedIn") is True
    except json.JSONDecodeError:
        return False


def search_prompt(query: str, recency_days: int | None, limit: int | None, domains: list[str] | None) -> str:
    lines = [
        "必须实际调用原生网页搜索工具检索后再作答，禁止凭记忆回答或编造链接。",
        f"查询：{query}",
        (f"最多 {limit} 条。" if limit is not None else "不要人为限制结果条数，返回本次搜索实际取得的全部相关来源。") + "snippet 引用原文短句。",
    ]
    if recency_days:
        lines.append(f"只保留最近 {recency_days} 天的结果。")
    if domains:
        lines.append("优先这些域名：" + ", ".join(domains))
    return "\n".join(lines)


def page_from(parsed: dict, url: str, max_chars: int, backend: str) -> dict:
    text, truncated = clip(parsed.get("markdown") or "", max_chars)
    return {
        "title": parsed.get("title") or hostname_of(url),
        "url": parsed.get("url") or url,
        "markdown": text,
        "truncated": truncated,
        "backend": backend,
        "untrusted": True,
    }


def hits_from(parsed: dict, limit: int | None) -> list[dict]:
    return dedupe_hits(parsed.get("results") or [])[:limit]


def auth_file_exists(path: Path) -> bool:
    return path.is_file()
