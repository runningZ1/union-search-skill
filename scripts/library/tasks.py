import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from library.archive import new_id
from library.db import jsonb
from library.defaults import DEFAULT_FETCH_OPTIONS

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
# 执行器每 5 秒写一次心跳；超过该时长没有心跳视为已中断
HEARTBEAT_STALE = timedelta(seconds=30)
WORKER_START_WAIT = 20
ITEM_STATUSES = ("pending", "running", "succeeded", "unchanged", "partial", "restricted", "failed", "pending_preprocess", "cancelled")
SUCCESS = ("succeeded", "unchanged")
FINAL = ("succeeded", "unchanged", "partial", "restricted", "failed", "pending_preprocess", "cancelled")
DEFAULT_OPTIONS = DEFAULT_FETCH_OPTIONS


class SelectionError(ValueError):
    pass


def resolve_search_selection(conn, search_id, display_ids):
    """把搜索运行内的展示 ID 转成资料；display_ids 为 None 表示全部。任何 ID 无效时不创建任务。"""
    run = conn.execute("SELECT id FROM search_runs WHERE id = %s", (search_id,)).fetchone()
    if run is None:
        raise LookupError(f"搜索运行不存在: {search_id}")
    rows = conn.execute(
        """SELECT document_id, min(coalesce(display_id, 2147483647)) AS first_id, min(platform || ':' || rank) AS first_hit,
                  array_agg(DISTINCT display_id) AS display_ids
           FROM search_hits WHERE search_id = %s GROUP BY document_id ORDER BY first_id, first_hit""", (search_id,)).fetchall()
    if display_ids is None:
        return [row["document_id"] for row in rows]
    by_display = {}
    for row in rows:
        for display_id in row["display_ids"]:
            if display_id is not None:
                by_display[display_id] = row["document_id"]
    missing = [value for value in display_ids if value not in by_display]
    if missing:
        raise SelectionError(f"搜索运行 {search_id} 中不存在这些结果 ID: {missing}")
    return list(dict.fromkeys(by_display[value] for value in display_ids))


def resolve_documents(conn, document_ids):
    found = {row["id"] for row in conn.execute("SELECT id FROM documents WHERE id = ANY(%s)", (list(document_ids),)).fetchall()}
    missing = [value for value in document_ids if value not in found]
    if missing:
        raise SelectionError(f"资料不存在: {missing}")
    return list(dict.fromkeys(document_ids))


def create_task(conn, search_id, scope, selection, document_ids, options, collect_until=None):
    """collect_until 不为空时任务处于收集状态：执行器在此之前持续等待新加入的任务项。"""
    task_id = new_id("task")
    with conn.transaction():
        conn.execute(
            """INSERT INTO fetch_tasks (id, search_id, scope, selection, options, status, collect_until)
               VALUES (%s, %s, %s, %s, %s, 'queued', %s)""",
            (task_id, search_id, scope, jsonb(selection), jsonb(options), collect_until))
        append_items(conn, task_id, document_ids)
    return task_id


def append_items(conn, task_id, document_ids):
    """把资料追加为任务项，序号接在已有项之后；已在任务中的资料跳过。返回新增项数。"""
    if not document_ids:
        return 0
    with conn.transaction():
        urls = {row["id"]: row["fetch_url"] for row in conn.execute("SELECT id, fetch_url FROM documents WHERE id = ANY(%s)",
                                                                    (list(document_ids),)).fetchall()}
        present = {row["document_id"] for row in conn.execute("SELECT document_id FROM fetch_task_items WHERE task_id = %s AND document_id = ANY(%s)",
                                                              (task_id, list(document_ids))).fetchall()}
        seq = conn.execute("SELECT coalesce(max(seq), 0) AS n FROM fetch_task_items WHERE task_id = %s", (task_id,)).fetchone()["n"]
        added = 0
        for doc_id in dict.fromkeys(document_ids):
            if doc_id in present:
                continue
            seq += 1
            added += 1
            conn.execute("INSERT INTO fetch_task_items (task_id, seq, document_id, url) VALUES (%s, %s, %s, %s)",
                         (task_id, seq, doc_id, urls[doc_id]))
    return added


def _alive(task):
    beat = task["worker_heartbeat"]
    return beat is not None and datetime.now(timezone.utc) - beat < HEARTBEAT_STALE


def start_worker(conn, config, task_id):
    """启动独立于当前终端的执行器进程，并等待它写入心跳确认已接管任务。"""
    return wait_worker(conn, task_id, *launch_worker(config, task_id))


def launch_worker(config, task_id):
    """启动执行器进程，不等待接管；返回 (令牌, 进程, 日志路径)。"""
    token = uuid.uuid4().hex
    log_path = config.logs_dir / f"{task_id}.log"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SCRIPTS_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    command = [sys.executable, "-m", "library.worker", "--task-id", task_id, "--token", token]
    with open(log_path, "ab") as log:
        if os.name == "nt":
            # CREATE_NO_WINDOW 给执行器一个不可见的控制台，node 等子进程继承它，不会各自弹出终端窗口
            flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_BREAKAWAY_FROM_JOB
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, env=env,
                                       cwd=str(SCRIPTS_DIR), creationflags=flags, close_fds=True)
        else:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, env=env,
                                       cwd=str(SCRIPTS_DIR), start_new_session=True, close_fds=True)
    return token, process, log_path


def wait_worker(conn, task_id, token, process, log_path):
    """等待执行器写入心跳确认已接管任务。"""
    deadline = time.monotonic() + WORKER_START_WAIT
    while time.monotonic() < deadline:
        row = conn.execute("SELECT worker_token, worker_pid FROM fetch_tasks WHERE id = %s", (task_id,)).fetchone()
        if row["worker_token"] == token:
            return {"started": True, "pid": row["worker_pid"], "log": str(log_path)}
        if process.poll() is not None:
            return {"started": False, "pid": process.pid, "log": str(log_path), "exit_code": process.returncode}
        time.sleep(0.2)
    return {"started": False, "pid": process.pid, "log": str(log_path), "exit_code": None}


def task_row(conn, task_id):
    task = conn.execute("SELECT * FROM fetch_tasks WHERE id = %s", (task_id,)).fetchone()
    if task is None:
        raise LookupError(f"抓取任务不存在: {task_id}")
    return task


def effective_status(task):
    """数据库里的状态加上心跳判断：运行中但执行器失联的任务为 interrupted。"""
    if task["status"] in ("running", "cancelling") and not _alive(task):
        return "interrupted"
    return task["status"]


def summarize(conn, task_id, include_items=True):
    task = task_row(conn, task_id)
    counts = {status: 0 for status in ITEM_STATUSES}
    for row in conn.execute("SELECT status, count(*) AS n FROM fetch_task_items WHERE task_id = %s GROUP BY status", (task_id,)).fetchall():
        counts[row["status"]] = row["n"]
    total = sum(counts.values())
    result = {
        "task_id": task_id,
        "search_id": task["search_id"],
        "scope": task["scope"],
        "selection": task["selection"],
        "options": task["options"],
        "status": effective_status(task),
        "cancel_requested": task["cancel_requested"],
        "collecting": task["collect_until"] is not None,
        "created_at": task["created_at"].isoformat(),
        "worker_started_at": task["worker_started_at"].isoformat() if task["worker_started_at"] else None,
        "worker_heartbeat": task["worker_heartbeat"].isoformat() if task["worker_heartbeat"] else None,
        "finished_at": task["finished_at"].isoformat() if task["finished_at"] else None,
        "total_items": total,
        "disposed_items": sum(counts[status] for status in FINAL),
        "body_success_items": sum(counts[status] for status in SUCCESS),
        "counts": counts,
    }
    if include_items:
        rows = conn.execute(
            """SELECT i.seq, i.document_id, i.url, i.status, i.started_at, i.finished_at, i.error,
                      a.id AS attempt_id, a.http_status, a.change_kind, a.technical_reason, a.restrictions, a.content_type,
                      a.duration_ms, a.similarity, a.diff_stats, a.error AS attempt_error
               FROM fetch_task_items i LEFT JOIN fetch_attempts a ON a.id = i.attempt_id
               WHERE i.task_id = %s ORDER BY i.seq""", (task_id,)).fetchall()
        result["items"] = [{
            "seq": row["seq"], "document_id": row["document_id"], "url": row["url"], "status": row["status"],
            "attempt_id": row["attempt_id"], "http_status": row["http_status"], "content_type": row["content_type"],
            "change_kind": row["change_kind"], "technical_reason": row["technical_reason"], "restrictions": row["restrictions"],
            "duration_ms": row["duration_ms"], "similarity": row["similarity"], "diff_stats": row["diff_stats"],
            "started_at": row["started_at"].isoformat() if row["started_at"] else None,
            "finished_at": row["finished_at"].isoformat() if row["finished_at"] else None,
            "error": row["attempt_error"] or row["error"],
        } for row in rows]
    return result


def reset_for_resume(conn, task_id):
    """恢复中断任务：只把未完成的执行中项放回待执行，已完成项保持不变。"""
    with conn.transaction():
        task = conn.execute("SELECT * FROM fetch_tasks WHERE id = %s FOR UPDATE", (task_id,)).fetchone()
        if _alive(task):
            return False
        conn.execute("""UPDATE fetch_attempts SET status = 'interrupted', finished_at = now()
                        WHERE id IN (SELECT attempt_id FROM fetch_task_items WHERE task_id = %s AND status = 'running')
                          AND finished_at IS NULL""", (task_id,))
        reset = conn.execute("UPDATE fetch_task_items SET status = 'pending', started_at = NULL, attempt_id = NULL WHERE task_id = %s AND status = 'running'",
                             (task_id,)).rowcount
        pending = conn.execute("SELECT count(*) AS n FROM fetch_task_items WHERE task_id = %s AND status = 'pending'", (task_id,)).fetchone()["n"]
        if pending:
            conn.execute("UPDATE fetch_tasks SET status = 'queued', finished_at = NULL WHERE id = %s", (task_id,))
    return {"reset_running": reset, "pending": pending}


def reset_failed(conn, task_id):
    """显式重试：只把失败项放回待执行。"""
    with conn.transaction():
        task = conn.execute("SELECT * FROM fetch_tasks WHERE id = %s FOR UPDATE", (task_id,)).fetchone()
        if _alive(task):
            raise RuntimeError(f"任务 {task_id} 的执行器仍在运行，结束后再重试失败项")
        count = conn.execute("UPDATE fetch_task_items SET status = 'pending', started_at = NULL, finished_at = NULL, attempt_id = NULL, error = NULL WHERE task_id = %s AND status = 'failed'",
                             (task_id,)).rowcount
        if count:
            conn.execute("UPDATE fetch_tasks SET status = 'queued', finished_at = NULL, cancel_requested = false WHERE id = %s", (task_id,))
    return count


def request_cancel(conn, task_id):
    with conn.transaction():
        task = conn.execute("SELECT * FROM fetch_tasks WHERE id = %s FOR UPDATE", (task_id,)).fetchone()
        if task["status"] in ("completed", "partial", "failed", "cancelled"):
            return task["status"]
        conn.execute("UPDATE fetch_tasks SET cancel_requested = true WHERE id = %s", (task_id,))
        if _alive(task):
            conn.execute("UPDATE fetch_tasks SET status = 'cancelling' WHERE id = %s", (task_id,))
            return "cancelling"
        # 没有执行器在运行，直接结束：未开始的项记为取消，已完成项保留
        conn.execute("UPDATE fetch_task_items SET status = 'cancelled', finished_at = now() WHERE task_id = %s AND status IN ('pending', 'running')", (task_id,))
        conn.execute("UPDATE fetch_tasks SET status = 'cancelled', finished_at = now() WHERE id = %s", (task_id,))
        return "cancelled"


def final_status(counts, cancelled):
    total = sum(counts.values())
    if cancelled:
        return "cancelled"
    if total and sum(counts.get(status, 0) for status in SUCCESS) == total:
        return "completed"
    if total and counts.get("failed", 0) == total:
        return "failed"
    return "partial" if total else "completed"


def list_tasks(conn, limit):
    rows = conn.execute("SELECT id FROM fetch_tasks ORDER BY created_at DESC LIMIT %s", (limit,)).fetchall()
    return [summarize(conn, row["id"], include_items=False) for row in rows]
