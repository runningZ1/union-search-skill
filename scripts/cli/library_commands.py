import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from errors import CliError, CliUsageError

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from library import index, tasks  # noqa: E402
from library.archive import archive_envelope  # noqa: E402
from library.config import LibraryNotConfigured, load_config, missing_env  # noqa: E402
from library.db import open_library  # noqa: E402

TERMINAL = ("completed", "partial", "failed", "cancelled")
ORPHAN_AGE_SECONDS = 3600


def _load_env(env_file):
    from union_search.union_search import load_env_file

    load_env_file(env_file)


def _open(env_file=".env"):
    _load_env(env_file)
    try:
        config = load_config()
    except LibraryNotConfigured as exc:
        raise CliError("LIBRARY_NOT_CONFIGURED", str(exc), details={"missing_env": missing_env()})
    return config, open_library(config)


def _fetch_options(args) -> Dict[str, int]:
    options = dict(tasks.DEFAULT_OPTIONS)
    for key in ("concurrency", "per_host", "timeout"):
        value = getattr(args, "fetch_" + key, None)
        if value is not None:
            if value < 1:
                raise CliUsageError(f"--fetch-{key.replace('_', '-')} 必须大于 0")
            options[key] = value
    return options


def _launch(conn, config, search_id, scope, selection, document_ids, options):
    task_id = tasks.create_task(conn, search_id, scope, selection, document_ids, options)
    executor = tasks.start_worker(conn, config, task_id) if document_ids else {"started": False, "reason": "no_items"}
    if not document_ids:
        with conn.transaction():
            conn.execute("UPDATE fetch_tasks SET status = 'completed', finished_at = now() WHERE id = %s", (task_id,))
    summary = tasks.summarize(conn, task_id, include_items=False)
    summary["executor"] = executor
    return summary


def _add_error(envelope, error):
    envelope["errors"].append(error)
    envelope.update(ok=False, success=False, type="error")
    primary = envelope["errors"][0]
    envelope["error"] = {"code": primary["code"], "message": primary["message"], "retryable": bool(primary.get("retryable")),
                         "outcome": primary.get("outcome", "unknown"), "details": {"failures": envelope["errors"]},
                         "next_actions": primary.get("next_actions", [])}


def search_params(args) -> Dict[str, Any]:
    names = ("platforms", "group", "limit", "preset", "max_workers", "timeout", "deduplicate", "param", "platform", "platform_command")
    return {name: getattr(args, name) for name in names if hasattr(args, name)}


def open_fetch_stream(args):
    """--fetch all：搜索开始前创建抓取任务并启动执行器。资料库未配置时返回 None，由归档步骤报告。"""
    from library.stream import FetchStream

    _load_env(args.env_file)
    try:
        config = load_config()
    except LibraryNotConfigured:
        return None
    options = _fetch_options(args)
    return FetchStream(open_library(config), config, options, args.timeout)


def archive_search(envelope, args) -> int:
    """搜索结果写入长期资料库；按需创建抓取任务。返回需要覆盖的退出码，0 表示不覆盖。"""
    _load_env(args.env_file)
    fetch_mode = getattr(args, "fetch", None)
    try:
        config = load_config()
    except LibraryNotConfigured as exc:
        envelope["meta"]["library"] = {"archived": False, "configured": False, "message": str(exc),
                                       "next_actions": [{"command": "union-search doctor"}]}
        if fetch_mode:
            _add_error(envelope, CliError("LIBRARY_NOT_CONFIGURED", str(exc) + "；未创建抓取任务").to_dict())
            return 3
        return 0
    if "data" not in envelope:
        return 0
    # 记录 .work 完整结果文件的内容哈希；以后导入该文件时识别为同一次搜索，不重复归档
    full_file = Path(envelope["meta"]["full_result_file"])
    source = "sha256:" + hashlib.sha256(full_file.read_bytes()).hexdigest()
    stream = getattr(args, "fetch_stream", None)
    started = time.monotonic()
    try:
        # 带抓取时沿用搜索开始前建立的连接，不再重新连接和检查表结构
        conn = stream.conn if stream is not None else open_library(config)
        archived, touched = archive_envelope(conn, envelope, {**search_params(args), "full_result_file": str(full_file)}, import_source=source)
    except Exception as exc:  # 归档失败必须明示，搜索结果仍在 full_result_file 中可用
        envelope["meta"]["library"] = {"archived": False, "configured": True, "error": f"{type(exc).__name__}: {exc}",
                                       "available_results": envelope["meta"].get("full_result_file")}
        cancelled = ""
        if stream is not None:
            stream.abort()
            cancelled = f"；提前开始的抓取任务 {stream.task_id} 已取消，已取得的正文保留"
        _add_error(envelope, CliError("ARCHIVE_FAILURE", f"搜索结果未写入长期资料库: {type(exc).__name__}: {exc}" + cancelled).to_dict())
        return 3
    archive_ms = round((time.monotonic() - started) * 1000)
    if stream is not None:
        # 先结束收集，执行器补齐剩余资料；检索索引随后写入，不推迟抓取
        task = stream.finish(archived["search_id"], tasks.resolve_search_selection(conn, archived["search_id"], None))
    index_started = time.monotonic()
    indexed = index.sync_documents(conn, config, touched)
    envelope["meta"]["library"] = {"archived": True, **archived, "index": indexed, "location": config.public(),
                                   "timing_ms": {"archive": archive_ms, "index": round((time.monotonic() - index_started) * 1000)}}
    if stream is not None:
        envelope["meta"]["fetch_task"] = task
        if task["total_items"] and not task["executor"]["started"]:
            _add_error(envelope, CliError("EXECUTOR_START_FAILED", f"抓取任务 {task['task_id']} 已排队，执行器未能启动",
                                          details=task["executor"]).to_dict())
            conn.close()
            return 3
    conn.close()
    return 0


def handle_fetch(args) -> Dict[str, Any]:
    config, conn = _open(args.env_file)
    options = _fetch_options(args)
    try:
        if args.document_ids:
            if args.search_id or args.ids or args.all:
                raise CliUsageError("--document-ids 不能与 --search-id/--ids/--all 同时使用")
            document_ids = tasks.resolve_documents(conn, args.document_ids)
            search_id, scope, selection = None, "documents", {"document_ids": args.document_ids}
        else:
            if not args.search_id or bool(args.ids) == bool(args.all):
                raise CliUsageError("使用 --search-id 时必须且只能选择 --ids 或 --all；或者使用 --document-ids")
            document_ids = tasks.resolve_search_selection(conn, args.search_id, None if args.all else args.ids)
            search_id, scope = args.search_id, "all" if args.all else "ids"
            selection = {"all": True} if args.all else {"ids": args.ids}
    except tasks.SelectionError as exc:
        raise CliError("UNKNOWN_ID", str(exc))
    except LookupError as exc:
        raise CliError("UNKNOWN_ID", str(exc))
    task = _launch(conn, config, search_id, scope, selection, document_ids, options)
    if args.wait and document_ids and task["executor"]["started"]:
        return _wait_result(conn, task["task_id"], args.wait_timeout, "fetch", extra={"executor": task["executor"]})
    errors = []
    if document_ids and not task["executor"]["started"]:
        errors.append(CliError("EXECUTOR_START_FAILED", f"抓取任务 {task['task_id']} 已排队，执行器未能启动", details=task["executor"]).to_dict())
    conn.close()
    return {"command": "fetch", "query": None, "success": not errors, "data": task, "errors": errors,
            "meta": {"accepted": True, "items": len(document_ids)}, "runtime_exit_code": 3 if errors else 0}


def _wait_result(conn, task_id, timeout, command, extra=None):
    deadline = None if timeout is None else time.monotonic() + timeout
    while True:
        summary = tasks.summarize(conn, task_id)
        if summary["status"] in TERMINAL or summary["status"] == "interrupted" or summary["status"] == "queued":
            break
        if deadline is not None and time.monotonic() >= deadline:
            break
        time.sleep(1)
    if extra:
        summary.update(extra)
    conn.close()
    errors = []
    status = summary["status"]
    if status not in TERMINAL:
        code = "TIMEOUT" if status == "running" else "FETCH_INCOMPLETE"
        errors.append(CliError(code, f"任务 {task_id} 当前状态为 {status}，尚未结束",
                               next_actions=[{"command": f"union-search task status {task_id}"}, {"command": f"union-search task resume {task_id}"}]).to_dict())
    elif summary["body_success_items"] != summary["total_items"]:
        errors.append(CliError("FETCH_INCOMPLETE",
                               f"任务 {task_id} 已结束：{summary['body_success_items']}/{summary['total_items']} 项取得正文，其余项见 counts",
                               details={"counts": summary["counts"]},
                               next_actions=[{"command": f"union-search task retry {task_id} --failed"}]).to_dict())
    return {"command": command, "query": None, "success": not errors, "data": summary, "errors": errors,
            "meta": {"task_id": task_id}, "runtime_exit_code": CliError(errors[0]["code"], "").exit_code if errors else 0}


def handle_task(args) -> Dict[str, Any]:
    config, conn = _open(args.env_file)
    if args.action == "list":
        data = tasks.list_tasks(conn, args.limit)
        conn.close()
        return {"command": "task list", "query": None, "success": True, "data": {"tasks": data}, "errors": [], "meta": {"count": len(data)}, "runtime_exit_code": 0}
    if not args.task_id:
        raise CliUsageError(f"task {args.action} 需要任务 ID")
    try:
        tasks.task_row(conn, args.task_id)
    except LookupError as exc:
        raise CliError("UNKNOWN_ID", str(exc))
    command = f"task {args.action}"
    if args.action == "status":
        data = tasks.summarize(conn, args.task_id)
        conn.close()
        return {"command": command, "query": None, "success": True, "data": data, "errors": [], "meta": {}, "runtime_exit_code": 0}
    if args.action == "wait":
        return _wait_result(conn, args.task_id, args.timeout, command)
    if args.action == "cancel":
        state = tasks.request_cancel(conn, args.task_id)
        data = tasks.summarize(conn, args.task_id, include_items=False)
        conn.close()
        return {"command": command, "query": None, "success": True, "data": {**data, "cancel_state": state}, "errors": [], "meta": {}, "runtime_exit_code": 0}
    if args.action == "resume":
        reset = tasks.reset_for_resume(conn, args.task_id)
        if reset is False:
            data = tasks.summarize(conn, args.task_id, include_items=False)
            conn.close()
            return {"command": command, "query": None, "success": True, "data": {**data, "resume": "executor_still_running"}, "errors": [], "meta": {}, "runtime_exit_code": 0}
        return _restart(conn, config, args.task_id, command, {"resume": reset}, reset["pending"])
    if args.action == "retry":
        try:
            count = tasks.reset_failed(conn, args.task_id)
        except RuntimeError as exc:
            raise CliUsageError(str(exc))
        return _restart(conn, config, args.task_id, command, {"retry_failed_items": count}, count)
    raise CliUsageError(f"未知的 task 操作: {args.action}")


def _restart(conn, config, task_id, command, info, pending):
    executor = tasks.start_worker(conn, config, task_id) if pending else {"started": False, "reason": "no_pending_items"}
    data = {**tasks.summarize(conn, task_id, include_items=False), **info, "executor": executor}
    conn.close()
    errors = []
    if pending and not executor["started"]:
        errors.append(CliError("EXECUTOR_START_FAILED", f"任务 {task_id} 的执行器未能启动", details=executor).to_dict())
    return {"command": command, "query": None, "success": not errors, "data": data, "errors": errors, "meta": {}, "runtime_exit_code": 3 if errors else 0}


def _document_row(conn, document_id):
    doc = conn.execute("SELECT * FROM documents WHERE id = %s", (document_id,)).fetchone()
    if doc is None:
        raise CliError("UNKNOWN_ID", f"资料不存在: {document_id}")
    return doc


def _iso(value):
    return value.isoformat() if value else None


def _document_meta(doc):
    return {"document_id": doc["id"], "url": doc["fetch_url"], "canonical_url": doc["url"], "domain": doc["domain"], "title": doc["title"],
            "content_type": doc["content_type"], "content_type_evidence": doc["content_type_evidence"],
            "restrictions": doc["restrictions"], "metadata": doc["metadata"], "last_attempt_status": doc["last_attempt_status"],
            "preprocess_state": doc["preprocess_state"], "first_seen_at": _iso(doc["first_seen_at"]), "last_seen_at": _iso(doc["last_seen_at"])}


def _read_body(conn, config, doc):
    if doc["body_path"]:
        return {"state": "available", "text": (config.root / doc["body_path"]).read_text(encoding="utf-8"), "chars": doc["body_chars"],
                "hash": doc["body_hash"], "extractor": doc["body_extractor"], "accepted_at": _iso(doc["body_accepted_at"]),
                "checked_at": _iso(doc["body_checked_at"])}
    partial = conn.execute("""SELECT id, finished_at, partial_body, restrictions FROM fetch_attempts
                              WHERE document_id = %s AND partial_body IS NOT NULL ORDER BY id DESC LIMIT 1""", (doc["id"],)).fetchone()
    body = {"state": "not_fetched" if doc["last_attempt_status"] is None else "unavailable", "text": None,
            "next_actions": [{"command": f"union-search fetch --document-ids {doc['id']}"}]}
    if partial:
        body["partial"] = {"attempt_id": partial["id"], "finished_at": _iso(partial["finished_at"]), "text": partial["partial_body"],
                           "restrictions": partial["restrictions"], "note": "受限页面的公开部分，不是完整正文"}
    return body


def _read_hits(conn, document_id):
    rows = conn.execute("""SELECT h.search_id, r.query, r.started_at, h.platform, h.rank, h.display_id, h.title, h.url, h.content,
                                  h.published, h.thumbnail, h.engine, h.raw
                           FROM search_hits h JOIN search_runs r ON r.id = h.search_id
                           WHERE h.document_id = %s ORDER BY r.started_at, h.platform, h.rank""", (document_id,)).fetchall()
    return [{**row, "started_at": _iso(row["started_at"])} for row in rows]


def handle_read_documents(args) -> Dict[str, Any]:
    if not (args.body or args.summaries):
        raise CliUsageError("读取资料时需指定 --body 和/或 --summaries")
    config, conn = _open(args.env_file)
    items = []
    for document_id in args.document_id:
        doc = _document_row(conn, document_id)
        item = _document_meta(doc)
        if args.body:
            item["body"] = _read_body(conn, config, doc)
        if args.summaries:
            item["hits"] = _read_hits(conn, document_id)
        items.append(item)
    conn.close()
    return {"command": "read", "query": None, "success": True, "data": {"items": items}, "errors": [],
            "meta": {"source": "library", "network": False}, "runtime_exit_code": 0}


def handle_library(args) -> Dict[str, Any]:
    if args.action == "search":
        return _library_search(args)
    if args.action == "status":
        return _library_status(args)
    if args.action == "reindex":
        return _library_reindex(args)
    if args.action == "import":
        return _library_import(args)
    if args.action == "repair":
        return _library_repair(args)
    if args.action == "backup":
        return _library_backup(args)
    if args.action == "restore":
        return _library_restore(args)
    if args.action == "export":
        return _library_export(args)
    raise CliUsageError(f"未知的 library 操作: {args.action}")


def _library_export(args):
    from library.export import build_export

    if not args.search_id or not args.export_file:
        raise CliUsageError("library export 需要 --search-id <search_id> 与 --export-file <文件>")
    config, conn = _open(args.env_file)
    try:
        document = build_export(conn, config, args.search_id, args.task_id)
    except (LookupError, ValueError) as exc:
        raise CliError("UNKNOWN_ID", str(exc))
    conn.close()
    target = Path(args.export_file).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    data = {"export_file": str(target), **document["search"]}
    return {"command": "library export", "query": None, "success": True, "data": data, "errors": [],
            "meta": {"network": False}, "runtime_exit_code": 0}


def _config_only(env_file):
    """备份与恢复自己管理连接；恢复的目标数据库必须保持为空，不能先建表。"""
    _load_env(env_file)
    try:
        return load_config()
    except LibraryNotConfigured as exc:
        raise CliError("LIBRARY_NOT_CONFIGURED", str(exc), details={"missing_env": missing_env()})


def _library_backup(args):
    from library import backup

    if not args.backup_dir:
        raise CliUsageError("library backup 需要 --backup-dir <目录>")
    config = _config_only(args.env_file)
    try:
        data = backup.create_backup(config, Path(args.backup_dir).resolve())
    except FileExistsError as exc:
        raise CliUsageError(str(exc))
    except backup.MissingTool as exc:
        raise CliError("MISSING_DEPENDENCY", str(exc))
    except backup.LibraryCorrupted as exc:
        raise CliError("ARCHIVE_FAILURE", f"备份中止: {exc}", next_actions=[{"command": "union-search library repair"}])
    return {"command": "library backup", "query": None, "success": True, "data": data, "errors": [], "meta": {}, "runtime_exit_code": 0}


def _library_restore(args):
    from library import backup

    if not args.from_dir:
        raise CliUsageError("library restore 需要 --from <备份目录>")
    config = _config_only(args.env_file)
    try:
        data = backup.restore_backup(config, Path(args.from_dir).resolve())
    except backup.BackupInvalid as exc:
        raise CliError("BACKUP_INVALID", str(exc))
    except backup.RestoreTargetNotEmpty as exc:
        raise CliError("RESTORE_TARGET_NOT_EMPTY", str(exc))
    except backup.MissingTool as exc:
        raise CliError("MISSING_DEPENDENCY", str(exc))
    except backup.LibraryCorrupted as exc:
        raise CliError("ARCHIVE_FAILURE", f"恢复未通过核对: {exc}")
    errors = []
    if data["index"]["failed"]:
        errors.append(CliError("INDEX_UNAVAILABLE", f"{data['index']['failed']} 份资料未能写入索引，数据库与正文已恢复",
                               details={"errors": data["index"]["errors"][:5]}).to_dict())
    return {"command": "library restore", "query": None, "success": not errors, "data": data, "errors": errors, "meta": {},
            "runtime_exit_code": 3 if errors else 0}


def _library_search(args):
    if not args.query:
        raise CliUsageError("library search 需要检索词")
    config, conn = _open(args.env_file)
    filters: List[Dict[str, Any]] = []
    if args.has_body is not None:
        filters.append({"term": {"has_body": args.has_body}})
    for field, values in (("content_type", args.content_type), ("fetch_status", args.fetch_status), ("platforms", args.platforms), ("domain", args.domain)):
        if values:
            filters.append({"terms": {field: values}})
    limit = None if not args.limit else args.limit
    try:
        total, rows = index.search(config, args.query, filters, limit)
    except LookupError as exc:
        raise CliError("INDEX_UNAVAILABLE", str(exc), next_actions=[{"command": "union-search library reindex --all"}])
    except Exception as exc:  # 检索服务故障明确报错，不转去互联网搜索
        raise CliError("INDEX_UNAVAILABLE", f"本地检索索引不可用: {type(exc).__name__}: {exc}",
                       next_actions=[{"command": "union-search library status"}])
    items = []
    for rank, row in enumerate(rows, 1):
        source = row["_source"]
        item = {"rank": rank, "document_id": source["document_id"], "title": source["title"], "url": source["url"],
                "domain": source["domain"], "platforms": source["platforms"], "content_type": source["content_type"],
                "restrictions": source["restrictions"], "fetch_status": source["fetch_status"], "has_body": source["has_body"],
                "body_chars": source["body_chars"], "first_seen_at": source["first_seen_at"], "last_seen_at": source["last_seen_at"],
                "body_accepted_at": source["body_accepted_at"], "score": row["_score"],
                "matched_fields": sorted(row.get("highlight", {})), "highlights": row.get("highlight", {})}
        if args.content == "full":
            item["summaries"] = source["summaries"]
        items.append(item)
    pending = conn.execute("SELECT count(*) AS n FROM documents WHERE index_state <> 'indexed'").fetchone()["n"]
    conn.close()
    return {"command": "library search", "query": args.query, "success": True, "data": {"items": items},
            "errors": [], "meta": {"total": total, "returned": len(items), "network": False, "documents_not_indexed": pending,
                                   "content_mode": args.content}, "runtime_exit_code": 0}


def _library_status(args):
    config, conn = _open(args.env_file)
    counts = conn.execute("""SELECT (SELECT count(*) FROM search_runs) AS search_runs, (SELECT count(*) FROM search_hits) AS search_hits,
                                    (SELECT count(*) FROM documents) AS documents,
                                    (SELECT count(*) FROM documents WHERE body_hash IS NOT NULL) AS documents_with_body,
                                    (SELECT count(*) FROM fetch_tasks) AS fetch_tasks, (SELECT count(*) FROM fetch_attempts) AS fetch_attempts""").fetchone()
    index_states = {row["index_state"]: row["n"] for row in conn.execute("SELECT index_state, count(*) AS n FROM documents GROUP BY index_state").fetchall()}
    conn.close()
    es_state: Dict[str, Any]
    try:
        es = index.client(config)
        exists = bool(es.indices.exists(index=config.es_index))
        es_state = {"reachable": True, "index_exists": exists,
                    "index_documents": es.count(index=config.es_index)["count"] if exists else 0}
    except Exception as exc:  # 状态命令如实报告检索服务故障
        es_state = {"reachable": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"command": "library status", "query": None, "success": es_state["reachable"],
            "data": {"location": config.public(), "counts": counts, "index_states": index_states, "elasticsearch": es_state},
            "errors": [] if es_state["reachable"] else [CliError("INDEX_UNAVAILABLE", es_state["error"]).to_dict()],
            "meta": {}, "runtime_exit_code": 0 if es_state["reachable"] else 3}


def _library_reindex(args):
    config, conn = _open(args.env_file)
    where = "" if args.all else "WHERE index_state <> 'indexed'"
    ids = [row["id"] for row in conn.execute(f"SELECT id FROM documents {where} ORDER BY id").fetchall()]
    if args.all:
        es = index.client(config)
        if es.indices.exists(index=config.es_index):
            es.indices.delete(index=config.es_index)
    totals = {"indexed": 0, "failed": 0, "errors": []}
    for start in range(0, len(ids), 200):
        result = index.sync_documents(conn, config, ids[start:start + 200], refresh=True)
        totals["indexed"] += result["indexed"]
        totals["failed"] += result["failed"]
        if result["error"]:
            totals["errors"].append(result["error"])
    conn.close()
    errors = [CliError("INDEX_UNAVAILABLE", f"{totals['failed']} 份资料未能写入索引", details={"errors": totals["errors"][:5]}).to_dict()] if totals["failed"] else []
    return {"command": "library reindex", "query": None, "success": not errors, "data": {"documents": len(ids), **totals},
            "errors": errors, "meta": {"mode": "all" if args.all else "pending"}, "runtime_exit_code": 3 if errors else 0}


def _import_files(paths):
    files = []
    for value in paths:
        path = Path(value).resolve()
        if path.is_dir():
            files.extend(sorted(path.rglob("full.json")))
        elif path.is_file():
            files.append(path)
        else:
            raise CliUsageError(f"导入路径不存在: {path}")
    return list(dict.fromkeys(files))


def _library_import(args):
    config, conn = _open(args.env_file)
    results = []
    touched_all = []
    for path in _import_files(args.paths):
        payload = path.read_bytes()
        source = "sha256:" + hashlib.sha256(payload).hexdigest()
        existing = conn.execute("SELECT id FROM search_runs WHERE import_source = %s", (source,)).fetchone()
        if existing:
            results.append({"file": str(path), "status": "already_imported", "search_id": existing["id"]})
            continue
        envelope = json.loads(payload.decode("utf-8"))
        data = envelope.get("data")
        if not isinstance(data, dict) or not (isinstance(data.get("results"), dict) or "platform" in data):
            results.append({"file": str(path), "status": "unsupported", "error": "文件不是 search/platform 命令的完整搜索信封"})
            continue
        archived, touched = archive_envelope(conn, envelope, {"imported_from": str(path)}, import_source=source)
        touched_all.extend(touched)
        results.append({"file": str(path), "status": "imported", "legacy_request_id": envelope.get("meta", {}).get("request_id"), **archived})
    indexed = index.sync_documents(conn, config, sorted(set(touched_all)))
    conn.close()
    unsupported = [row for row in results if row["status"] == "unsupported"]
    errors = [CliError("INVALID_ARGUMENT", f"{len(unsupported)} 个文件不是可导入的搜索信封", details={"files": [row["file"] for row in unsupported]}).to_dict()] if unsupported else []
    return {"command": "library import", "query": None, "success": not errors, "data": {"files": results, "index": indexed},
            "errors": errors, "meta": {"files": len(results)}, "runtime_exit_code": 2 if errors else 0}


def _library_repair(args):
    """核对正文文件：清理没有被引用的旧版本文件，报告被引用但缺失或哈希不符的文件。"""
    from library.compare import body_hash
    from library.db import file_delete_guard

    config, conn = _open(args.env_file)
    with file_delete_guard(conn) as granted:
        if not granted:
            conn.close()
            raise CliError("BACKUP_IN_PROGRESS", "资料库备份正在进行，备份结束后再清理正文文件")
        result = _repair_files(conn, config, body_hash)
    conn.close()
    return result


def _repair_files(conn, config, body_hash):
    rows = conn.execute("SELECT id, body_path, body_hash FROM documents WHERE body_path IS NOT NULL").fetchall()
    referenced = {row["body_path"] for row in rows}
    missing, mismatched = [], []
    for row in rows:
        target = config.root / row["body_path"]
        if not target.exists():
            missing.append(row["id"])
        elif body_hash(target.read_text(encoding="utf-8")) != row["body_hash"]:
            mismatched.append(row["id"])
    # 只处理一小时前的文件：执行中的任务可能刚写入正文、尚未提交指针
    cutoff = time.time() - ORPHAN_AGE_SECONDS
    orphans = [path for path in config.bodies_dir.rglob("*.md")
               if path.relative_to(config.root).as_posix() not in referenced and path.stat().st_mtime < cutoff]
    for path in orphans:
        path.unlink()
    staging = [path for path in config.staging_dir.iterdir() if path.stat().st_mtime < cutoff]
    for path in staging:
        path.unlink()
    errors = []
    if missing or mismatched:
        errors.append(CliError("ARCHIVE_FAILURE", "存在缺失或内容不符的正文文件，需要从备份恢复或重新抓取",
                               details={"missing": missing, "mismatched": mismatched}).to_dict())
    return {"command": "library repair", "query": None, "success": not errors,
            "data": {"checked": len(rows), "missing": missing, "mismatched": mismatched,
                     "removed_orphans": [str(path) for path in orphans], "removed_staging": [str(path) for path in staging]},
            "errors": errors, "meta": {}, "runtime_exit_code": 3 if errors else 0}
