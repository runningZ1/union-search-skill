import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from library.compare import body_hash, diff_stats, normalize_body
from library.db import file_delete_guard, jsonb

SUCCESS_STATUSES = ("succeeded", "unchanged")


def start_attempt(conn, task_id, document_id):
    """先登记尝试，序号按开始先后递增，用于判断迟到的旧结果。"""
    with conn.transaction():
        row = conn.execute(
            "INSERT INTO fetch_attempts (task_id, document_id, started_at, status) VALUES (%s, %s, now(), 'running') RETURNING id, started_at",
            (task_id, document_id)).fetchone()
    return row["id"], row["started_at"]


def _write_body_file(config, document_id, digest, text):
    """正文写入以哈希命名的新文件；先写暂存文件再原子改名，读取方不会看到半份正文。"""
    relative = Path("bodies") / document_id[4:6] / document_id / f"{digest}.md"
    target = config.root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = config.staging_dir / f"body-{uuid.uuid4().hex}.md"
    staging.write_text(text, encoding="utf-8", newline="\n")
    os.replace(staging, target)
    return relative.as_posix()


def finish_attempt(conn, config, attempt_id, started_at, document_id, outcome):
    """按抓取结论更新资料。返回 (任务项状态, 变化类别, 需删除的旧正文路径)。"""
    finished = datetime.now(timezone.utc)
    status = outcome["status"]
    new_text = normalize_body(outcome["body"]) if status == "succeeded" else None
    new_digest = body_hash(new_text) if new_text is not None else None
    new_path = None
    if new_text is not None:
        doc = conn.execute("SELECT body_hash FROM documents WHERE id = %s", (document_id,)).fetchone()
        if doc["body_hash"] != new_digest:
            new_path = _write_body_file(config, document_id, new_digest, new_text)

    stale_file = None
    with conn.transaction():
        doc = conn.execute("SELECT * FROM documents WHERE id = %s FOR UPDATE", (document_id,)).fetchone()
        change_kind = None
        stats = None
        similarity = None
        item_status = status
        updates = {"last_attempt_id": attempt_id, "last_attempt_status": status, "index_state": "pending"}
        if outcome.get("content_type"):
            updates["content_type"] = outcome["content_type"]
            updates["content_type_evidence"] = jsonb(outcome["content_type_evidence"])
        if outcome.get("http_status") is not None or status == "pending_preprocess":
            updates["restrictions"] = jsonb(outcome["restrictions"])
        if outcome.get("metadata"):
            updates["metadata"] = jsonb({**doc["metadata"], **outcome["metadata"]})
            if outcome["metadata"].get("title"):
                updates["title"] = outcome["metadata"]["title"]
        updates["preprocess_state"] = outcome.get("preprocess_state") or ("pending" if status == "pending_preprocess" else doc["preprocess_state"])

        newer_accepted = doc["accepted_attempt_id"] is not None and doc["accepted_attempt_id"] > attempt_id
        if status == "succeeded" and newer_accepted:
            # 更晚开始的抓取已被接受，这个迟到结果不覆盖
            change_kind = "stale"
            item_status = "unchanged"
            stale_file = new_path if new_path != doc["body_path"] else None
        elif status == "succeeded" and doc["body_hash"] == new_digest:
            change_kind = "unchanged"
            item_status = "unchanged"
            updates.update(body_checked_at=finished, accepted_attempt_id=attempt_id)
        elif status == "succeeded":
            if new_path is None:
                # 预检查后正文被并发更新，重新写入本次正文
                new_path = _write_body_file(config, document_id, new_digest, new_text)
            if doc["body_hash"]:
                old_text = (config.root / doc["body_path"]).read_text(encoding="utf-8")
                stats, similarity = diff_stats(old_text, new_text)
                change_kind = "changed"
                if doc["body_extractor"] and doc["body_extractor"] != outcome["extractor"]:
                    stats["extractor_changed"] = {"from": doc["body_extractor"], "to": outcome["extractor"]}
                stale_file = doc["body_path"]
            else:
                change_kind = "first"
            updates.update(body_hash=new_digest, body_path=new_path, body_chars=len(new_text), body_extractor=outcome["extractor"],
                           body_accepted_at=finished, body_checked_at=finished, accepted_attempt_id=attempt_id,
                           body_etag=outcome.get("etag"), body_last_modified=outcome.get("last_modified"))
        elif status == "not_modified":
            change_kind = "not_modified"
            item_status = "unchanged"
            updates.update(body_checked_at=finished)

        assignments = ", ".join(f"{key} = %s" for key in updates)
        conn.execute(f"UPDATE documents SET {assignments} WHERE id = %s", (*updates.values(), document_id))
        conn.execute(
            """UPDATE fetch_attempts SET finished_at = %s, duration_ms = %s, status = %s, http_status = %s, final_url = %s,
                   response_type = %s, content_type = %s, restrictions = %s, technical_reason = %s, evidence = %s, extractor = %s,
                   body_hash = %s, previous_hash = %s, change_kind = %s, diff_stats = %s, similarity = %s, partial_body = %s, error = %s
               WHERE id = %s""",
            (finished, int((finished - started_at).total_seconds() * 1000), item_status, outcome.get("http_status"),
             outcome.get("final_url"), outcome.get("response_type"), outcome.get("content_type"), jsonb(outcome["restrictions"]),
             outcome.get("technical_reason"), jsonb(outcome["evidence"] + outcome["content_type_evidence"]), outcome.get("extractor"),
             new_digest, doc["body_hash"], change_kind, jsonb(stats) if stats else None, similarity,
             outcome.get("partial_body"), outcome.get("error"), attempt_id),
        )
    return item_status, change_kind, stale_file


def remove_stale_file(conn, config, relative):
    """新正文生效后删除旧版本文件；其他资料不会引用该路径。
    备份进行中时保留文件（备份快照可能仍引用它），返回 deferred，之后由 library repair 清理。"""
    if not relative:
        return None
    with file_delete_guard(conn) as granted:
        if not granted:
            return "deferred"
        (config.root / relative).unlink(missing_ok=True)
    return "removed"
