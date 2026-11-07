from datetime import datetime, timezone

EXPORT_FORMAT = "union-search.search-export"
EXPORT_VERSION = 2


def _iso(value):
    return value.isoformat() if value else None


def _task(conn, search_id, task_id):
    # 指定任务；未指定时取该次搜索最近创建的抓取任务，没有任务返回 None
    if task_id:
        task = conn.execute("SELECT * FROM fetch_tasks WHERE id = %s", (task_id,)).fetchone()
        if task is None:
            raise LookupError(f"抓取任务不存在: {task_id}")
        if task["search_id"] != search_id:
            raise ValueError(f"抓取任务 {task_id} 不属于搜索 {search_id}")
        return task
    return conn.execute("SELECT * FROM fetch_tasks WHERE search_id = %s ORDER BY created_at DESC LIMIT 1", (search_id,)).fetchone()


def _channel_order(run, channels):
    data = run["snapshot"].get("data") or {}
    ordered = [row["platform"] for row in data.get("channels") or []] or list(data.get("platforms") or [])
    ordered = [name for name in dict.fromkeys(ordered) if name in channels]
    return ordered + sorted(name for name in channels if name not in ordered)


def _result(config, hit, doc, item, task):
    # 每条结果字段固定、顺序固定，缺失值为 null
    if task is None:
        fetch_status = None
    elif item is None:
        fetch_status = "not_in_task"
    else:
        fetch_status = item["status"]
    return {
        "index": hit["rank"],
        "title": hit["title"],
        "url": hit["url"],
        "content": hit["content"],
        "published": hit["published"],
        "result_id": hit["display_id"],
        "document_id": hit["document_id"],
        "fetch_status": fetch_status,
        "fetch_reason": (item["technical_reason"] or item["error"]) if item else None,
        "body_file": str(config.root / doc["body_path"]) if doc["body_path"] else None,
        "body_chars": doc["body_chars"],
    }


def build_export(conn, config, search_id, task_id=None):
    # 按搜索渠道分组：每组字段相同，组内结果按渠道排名排列
    run = conn.execute("SELECT * FROM search_runs WHERE id = %s", (search_id,)).fetchone()
    if run is None:
        raise LookupError(f"搜索运行不存在: {search_id}")
    task = _task(conn, search_id, task_id)
    channels = {row["platform"]: row for row in conn.execute("SELECT * FROM search_channels WHERE search_id = %s", (search_id,)).fetchall()}
    hits = conn.execute("SELECT * FROM search_hits WHERE search_id = %s ORDER BY platform, rank", (search_id,)).fetchall()
    docs = {row["id"]: row for row in conn.execute("SELECT * FROM documents WHERE id = ANY(%s)",
                                                   (list({hit["document_id"] for hit in hits}),)).fetchall()}
    items = {}
    if task:
        for row in conn.execute(
                """SELECT i.document_id, i.status, i.error, a.technical_reason
                   FROM fetch_task_items i LEFT JOIN fetch_attempts a ON a.id = i.attempt_id WHERE i.task_id = %s""",
                (task["id"],)).fetchall():
            items[row["document_id"]] = row

    by_platform = {}
    for hit in hits:
        by_platform.setdefault(hit["platform"], []).append(
            _result(config, hit, docs[hit["document_id"]], items.get(hit["document_id"]), task))

    groups = []
    for number, platform in enumerate(_channel_order(run, channels), start=1):
        row = channels[platform]
        error = row["error"] or {}
        results = by_platform.get(platform, [])
        groups.append({
            "group": number,
            "channel": platform,
            "status": row["status"],
            "result_count": len(results),
            "duration_ms": row["duration_ms"],
            "error_code": error.get("code"),
            "error_message": error.get("message"),
            "results": results,
        })

    fetch_counts = {}
    for row in items.values():
        fetch_counts[row["status"]] = fetch_counts.get(row["status"], 0) + 1
    return {
        "format": EXPORT_FORMAT,
        "version": EXPORT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "search": {
            "query": run["query"],
            "search_id": run["id"],
            "started_at": _iso(run["started_at"]),
            "ok": run["search_ok"],
            "group_count": len(groups),
            "groups_with_results": sum(1 for group in groups if group["results"]),
            "groups_failed": sum(1 for group in groups if group["status"] == "failed"),
            "result_count": len(hits),
            "unique_document_count": len(docs),
            "fetch_task_id": task["id"] if task else None,
            "fetch_task_status": task["status"] if task else None,
            "fetch_counts": fetch_counts,
            "full_result_file": run["params"].get("full_result_file"),
        },
        "groups": groups,
    }
