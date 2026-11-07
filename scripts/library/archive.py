import hashlib
import re
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

from library.classify import guess_from_hit
from library.db import jsonb
from union_search.structured_results import canonical_url

# 原始字段里出现这些键名时不入库，防止保存凭据或授权信息
_SECRET_KEY = re.compile(r"(api[_-]?key|token|secret|authorization|password|cookie|credential)", re.I)


def new_id(prefix):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"{prefix}_{stamp}_{uuid.uuid4().hex[:8]}"


def document_id(url):
    return "doc_" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]


def scrub(value):
    if isinstance(value, dict):
        return {key: scrub(item) for key, item in value.items() if not _SECRET_KEY.search(str(key))}
    if isinstance(value, list):
        return [scrub(item) for item in value]
    return value


def _domain(url):
    host = (urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def channel_results(data):
    """返回 [(platform, channel_result)]；兼容 search 的多渠道结构和单渠道命令结构。"""
    if isinstance(data.get("results"), dict):
        order = data.get("platforms") or list(data["results"])
        return [(platform, data["results"][platform]) for platform in order if platform in data["results"]]
    return [(data["platform"], data)]


def _display_ids(data, channels):
    """命中与展示 ID 的对应关系：去重时按网址，不去重时按合并顺序。"""
    final_items = data.get("final_items")
    if final_items is None:
        platform, result = channels[0]
        return {(platform, index): index for index, _ in enumerate(result.get("items", []), 1)}
    mapping = {}
    if data.get("summary", {}).get("deduplicate_enabled", True):
        by_url = {canonical_url(row["url"]): row["id"] for row in final_items}
        for platform, result in channels:
            if not result.get("success"):
                continue
            for rank, item in enumerate(result.get("items", []), 1):
                mapping[(platform, rank)] = by_url.get(canonical_url(item["url"]))
        return mapping
    sequence = iter(row["id"] for row in final_items)
    for platform, result in channels:
        if not result.get("success"):
            continue
        for rank, _ in enumerate(result.get("items", []), 1):
            mapping[(platform, rank)] = next(sequence)
    return mapping


def upsert_document(conn, item, platform):
    """登记一条搜索结果对应的资料，返回资料 ID。
    同一页面的不同写法（www、末尾斜杠、跟踪参数）归为同一资料；请求时使用渠道给出的地址。"""
    key = canonical_url(item["url"])
    doc_id = document_id(key)
    kind, evidence = guess_from_hit(item["url"], platform)
    conn.execute(
        """INSERT INTO documents (id, url, fetch_url, domain, title, content_type, content_type_evidence)
           VALUES (%s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT (id) DO UPDATE SET last_seen_at = now(), index_state = 'pending',
               content_type = CASE WHEN documents.content_type = 'unknown' THEN EXCLUDED.content_type ELSE documents.content_type END,
               content_type_evidence = CASE WHEN documents.content_type = 'unknown' THEN EXCLUDED.content_type_evidence ELSE documents.content_type_evidence END""",
        (doc_id, key, item["url"], _domain(key), item["title"], kind, jsonb(evidence)),
    )
    return doc_id


def archive_envelope(conn, envelope, params, import_source=None, started_at=None):
    """把一次搜索的完整信封写入资料库。整个运行在一个事务里，失败时不留下半次归档。"""
    data = envelope["data"]
    channels = channel_results(data)
    display = _display_ids(data, channels)
    search_id = new_id("srch")
    raw_total = sum(len(result.get("items", [])) for _, result in channels if result.get("success"))
    unique_total = len(data["final_items"]) if "final_items" in data else raw_total
    started = started_at or envelope["timestamp"]
    touched = set()
    with conn.transaction():
        conn.execute(
            """INSERT INTO search_runs (id, command, query, params, started_at, search_ok, raw_total, unique_total,
                   snapshot, import_source, legacy_request_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (search_id, envelope["command"], envelope.get("query"), jsonb(params), started, bool(envelope["ok"]),
             raw_total, unique_total, jsonb(scrub(envelope)), import_source, envelope.get("meta", {}).get("request_id")),
        )
        for platform, result in channels:
            error = result.get("error_details") or ({"message": result["error"]} if result.get("error") else None)
            conn.execute(
                """INSERT INTO search_channels (search_id, platform, status, item_count, duration_ms, error, warning)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (search_id, platform, result.get("status") or ("success" if result.get("success") else "failed"),
                 len(result.get("items", [])), result.get("timing_ms"), jsonb(error) if error else None, result.get("warning")),
            )
            if not result.get("success"):
                continue
            for rank, item in enumerate(result.get("items", []), 1):
                doc_id = upsert_document(conn, item, platform)
                source = item["sources"][0] if item.get("sources") else {}
                conn.execute(
                    """INSERT INTO search_hits (search_id, platform, rank, display_id, document_id, title, url, content,
                           published, thumbnail, engine, raw)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (search_id, platform, rank, display.get((platform, rank)), doc_id, item["title"], item["url"],
                     item.get("content") or "", None if item.get("published") is None else str(item["published"]),
                     item.get("thumbnail"), source.get("engine"), jsonb(scrub(item["raw"])) if "raw" in item else None),
                )
                touched.add(doc_id)
    return {"search_id": search_id, "hits": raw_total, "unique_results": unique_total, "documents": len(touched)}, sorted(touched)
