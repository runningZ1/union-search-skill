import argparse
import json
import os
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urlsplit

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from library.config import load_config
from library.db import connect, ensure_schema
from library.preprocessors import PREPROCESSORS
from library.preprocessors import load as load_preprocessor
from library.tasks import HEARTBEAT_STALE, final_status

MEDIA_TYPES = ("video", "podcast")
# 任务项只在读写数据库的短时间内占用连接，网络请求和提取期间不占用
DB_POOL_SIZE = 16
# 没有可派发的项时，调度循环最多等待这么久再检查新加入的项和取消请求
IDLE_WAIT = 0.1


def log(message):
    print(f"{datetime.now(timezone.utc).isoformat()} {message}", flush=True)


def claim_task(conn, task_id, token):
    """登记为任务执行器；已有存活执行器时退出，避免同一任务被重复执行。"""
    with conn.transaction():
        task = conn.execute("SELECT * FROM fetch_tasks WHERE id = %s FOR UPDATE", (task_id,)).fetchone()
        if task is None:
            raise LookupError(f"抓取任务不存在: {task_id}")
        beat = task["worker_heartbeat"]
        if beat is not None and datetime.now(timezone.utc) - beat < HEARTBEAT_STALE and task["status"] in ("running", "cancelling"):
            return None
        conn.execute("""UPDATE fetch_tasks SET status = 'running', worker_pid = %s, worker_token = %s, worker_heartbeat = now(),
                        worker_started_at = now() WHERE id = %s""", (os.getpid(), token, task_id))
    return task


def heartbeat(config, task_id, token, stop):
    conn = connect(config)
    while not stop.wait(5):
        with conn.transaction():
            conn.execute("UPDATE fetch_tasks SET worker_heartbeat = now() WHERE id = %s AND worker_token = %s", (task_id, token))
    conn.close()


def _hits(conn, document_id):
    return conn.execute("""SELECT h.search_id, h.platform, h.rank, h.title, h.url, h.content, h.published, h.raw
                           FROM search_hits h WHERE h.document_id = %s ORDER BY h.search_id, h.platform, h.rank""",
                        (document_id,)).fetchall()


def media_outcome(doc):
    return {"status": "pending_preprocess", "http_status": None, "final_url": doc["fetch_url"], "response_type": None,
            "content_type": doc["content_type"], "content_type_evidence": doc["content_type_evidence"], "restrictions": [],
            "technical_reason": None, "evidence": ["preprocessor_not_installed:" + doc["content_type"]], "body": None,
            "partial_body": None, "metadata": {}, "extractor": None, "etag": None, "last_modified": None, "error": None}


def preprocess_outcome(config, doc, hits, options, fetched=None):
    """调用已注册的预处理模块；fetched 是网页请求阶段已确认的类型证据。"""
    result = load_preprocessor(doc["content_type"])(doc, hits, config.staging_dir, options["timeout"])
    status = result["status"]
    return {"status": status, "http_status": result.get("http_status"), "final_url": result.get("final_url") or doc["fetch_url"],
            "response_type": result.get("response_type"), "content_type": doc["content_type"],
            "content_type_evidence": fetched["content_type_evidence"] if fetched else doc["content_type_evidence"],
            "restrictions": result.get("restrictions") or [], "technical_reason": result.get("technical_reason"),
            "evidence": ["preprocessor:" + result["extractor"]] + (result.get("evidence") or []),
            "body": result.get("body") if status == "succeeded" else None,
            "partial_body": result.get("body") if status == "partial" else None,
            "metadata": result.get("metadata") or {}, "extractor": result["extractor"],
            "etag": result.get("etag"), "last_modified": result.get("last_modified"), "error": result.get("error"),
            "preprocess_state": "done" if status in ("succeeded", "not_modified") else "failed"}


def needs_network(content_type):
    return not (content_type in MEDIA_TYPES and content_type not in PREPROCESSORS)


def process_item(db, config, task_id, item, options, indexer):
    clock = [time.monotonic()]
    timing = {}

    def mark(stage):
        now = time.monotonic()
        timing[stage] = round((now - clock[0]) * 1000)
        clock[0] = now

    # 第一段：登记尝试并读取抓取所需的资料字段
    with db.connection() as conn:
        doc = conn.execute("SELECT * FROM documents WHERE id = %s", (item["document_id"],)).fetchone()
        attempt_id, started_at = store.start_attempt(conn, task_id, doc["id"])
        with conn.transaction():
            conn.execute("UPDATE fetch_task_items SET attempt_id = %s WHERE task_id = %s AND seq = %s", (attempt_id, task_id, item["seq"]))
        hits = _hits(conn, doc["id"]) if doc["content_type"] in PREPROCESSORS else None
        summary_chars = conn.execute("SELECT max(length(content)) AS n FROM search_hits WHERE document_id = %s", (doc["id"],)).fetchone()["n"]
    mark("prepare")
    # 第二段：网络请求与提取，不占用数据库连接
    try:
        if doc["content_type"] in PREPROCESSORS:
            outcome = preprocess_outcome(config, doc, hits, options)
        elif doc["content_type"] in MEDIA_TYPES:
            # 视频和播客不按网页抓取，也不下载媒体文件；保留搜索元数据等待预处理模块
            outcome = media_outcome(doc)
        else:
            # 已有正文由当前提取器生成时才发条件请求；提取器变化后需要重新取得页面
            conditional = bool(doc["body_hash"]) and doc["body_extractor"] == fetcher.EXTRACTOR
            outcome = fetcher.fetch(doc["fetch_url"], options["timeout"],
                                    etag=doc["body_etag"] if conditional else None,
                                    last_modified=doc["body_last_modified"] if conditional else None,
                                    previous_chars=doc["body_chars"], summary_chars=summary_chars)
            if outcome["status"] == "pending_preprocess" and outcome["content_type"] in PREPROCESSORS:
                with db.connection() as conn:
                    hits = _hits(conn, doc["id"])
                outcome = preprocess_outcome(config, {**doc, "content_type": outcome["content_type"]}, hits, options, fetched=outcome)
    except Exception:
        # 单项内部错误只影响该项，任务继续处理其他项
        outcome = media_outcome(doc)
        outcome.update(status="failed", technical_reason="internal_error", evidence=[], content_type=None,
                       content_type_evidence=[], error=traceback.format_exc()[-4000:])
    mark("fetch")
    # 第三段：比较与覆盖正文、结束任务项；检索索引交给索引线程批量写入
    with db.connection() as conn:
        mark("wait_db")
        item_status, change_kind, stale = store.finish_attempt(conn, config, attempt_id, started_at, doc["id"], outcome)
        with conn.transaction():
            conn.execute("UPDATE fetch_task_items SET status = %s, finished_at = now(), error = %s WHERE task_id = %s AND seq = %s",
                         (item_status, outcome.get("error"), task_id, item["seq"]))
        removal = store.remove_stale_file(conn, config, stale)
        mark("store")
    indexer.add(doc["id"])
    log(f"item {item['seq']} {doc['fetch_url']} ->{item_status} change={change_kind} old_file={removal} "
        f"timing={json.dumps({**timing, **outcome.get('timing_ms', {})})}")


class Indexer:
    """检索索引由单个线程写入：任务项结束后登记资料 ID，线程把上一批写入期间积累的资料合成一次 bulk 请求。
    抓取线程不等待索引，也不在索引期间占用数据库连接。"""

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.pending = []
        self.changed = threading.Condition()
        self.closing = False
        self.closed = False
        self.error = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def add(self, document_id):
        with self.changed:
            if self.error is not None:
                raise RuntimeError("检索索引线程已失败") from self.error
            self.pending.append(document_id)
            self.changed.notify()

    def _run(self):
        try:
            while True:
                with self.changed:
                    while not self.pending and not self.closing:
                        self.changed.wait()
                    if not self.pending:
                        return
                    batch, self.pending = list(dict.fromkeys(self.pending)), []
                started = time.monotonic()
                with self.db.connection() as conn:
                    result = index.sync_documents(conn, self.config, batch)
                log(f"index batch={len(batch)} indexed={result['indexed']} failed={result['failed']} "
                    f"ms={round((time.monotonic() - started) * 1000)} error={result['error']}")
        except BaseException as exc:
            # 数据库等非索引服务故障：记录后由 add 与 close 在执行器主流程中抛出
            self.error = exc
            raise

    def close(self):
        """写完已登记的资料后结束线程；线程失败时抛出它的异常。"""
        if self.closed:
            return
        self.closed = True
        with self.changed:
            self.closing = True
            self.changed.notify()
        self.thread.join()
        if self.error is not None:
            raise self.error


class HostSlots:
    """同一主机的并发上限。派发时跳过已满主机的项，先处理其他主机。"""

    def __init__(self, per_host):
        self.per_host = per_host
        self.active = {}

    def try_acquire(self, host):
        if self.active.get(host, 0) >= self.per_host:
            return False
        self.active[host] = self.active.get(host, 0) + 1
        return True

    def release(self, host):
        self.active[host] -= 1


class Scheduler:
    """单线程调度：从数据库读取待执行项放入内存队列，按并发上限与主机上限派发给执行线程。
    任务处于收集状态时，队列为空也继续等待新加入的项。"""

    def __init__(self, db, config, task_id, options, indexer):
        self.db = db
        self.config = config
        self.task_id = task_id
        self.options = options
        self.indexer = indexer
        self.slots = HostSlots(options["per_host"])
        self.backlog = []
        self.loaded_seq = 0
        self.running = 0
        self.changed = threading.Condition()
        self.failure = None

    def _poll(self):
        """读取取消标记、收集状态和新加入的待执行项。返回 (已请求取消, 仍在收集)。"""
        with self.db.connection() as conn:
            task = conn.execute("SELECT cancel_requested, collect_until FROM fetch_tasks WHERE id = %s", (self.task_id,)).fetchone()
            collecting = task["collect_until"] is not None
            if collecting and task["collect_until"] <= datetime.now(timezone.utc):
                # 搜索方没有按时结束收集（例如 CLI 被终止），到截止时间后按已收到的项完成任务
                conn.execute("UPDATE fetch_tasks SET collect_until = NULL WHERE id = %s", (self.task_id,))
                log(f"task {self.task_id} collect deadline passed")
                collecting = False
            rows = conn.execute(
                """SELECT i.seq, i.document_id, i.url, d.content_type FROM fetch_task_items i JOIN documents d ON d.id = i.document_id
                   WHERE i.task_id = %s AND i.status = 'pending' AND i.seq > %s ORDER BY i.seq""",
                (self.task_id, self.loaded_seq)).fetchall()
        for row in rows:
            row["host"] = (urlsplit(row["url"]).hostname or "") if needs_network(row["content_type"]) else None
        self.backlog.extend(rows)
        if rows:
            self.loaded_seq = rows[-1]["seq"]
        return task["cancel_requested"], collecting

    def _take(self):
        """按序号取出第一个主机未满的项。"""
        for position, item in enumerate(self.backlog):
            if item["host"] is None or self.slots.try_acquire(item["host"]):
                return self.backlog.pop(position)
        return None

    def _done(self, item, future):
        with self.changed:
            self.running -= 1
            if item["host"] is not None:
                self.slots.release(item["host"])
            if future.exception() is not None and self.failure is None:
                self.failure = future.exception()
            self.changed.notify()

    def run(self):
        concurrency = self.options["concurrency"]
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            while True:
                cancelled, collecting = self._poll()
                if cancelled:
                    break
                dispatch = []
                with self.changed:
                    if self.failure is not None:
                        break
                    while self.running < concurrency:
                        item = self._take()
                        if item is None:
                            break
                        self.running += 1
                        dispatch.append(item)
                if dispatch:
                    with self.db.connection() as conn:
                        conn.execute("UPDATE fetch_task_items SET status = 'running', started_at = now() WHERE task_id = %s AND seq = ANY(%s)",
                                     (self.task_id, [item["seq"] for item in dispatch]))
                    for item in dispatch:
                        future = pool.submit(process_item, self.db, self.config, self.task_id, item, self.options, self.indexer)
                        future.add_done_callback(lambda done, item=item: self._done(item, done))
                with self.changed:
                    if not self.backlog and self.running == 0 and not collecting:
                        break
                    if not dispatch:
                        self.changed.wait(IDLE_WAIT)
        # 执行线程中数据库或文件写入的异常不能被吞掉，任务按中断处理并保留现场
        if self.failure is not None:
            raise self.failure


def finish_task(conn, task_id):
    with conn.transaction():
        task = conn.execute("SELECT cancel_requested FROM fetch_tasks WHERE id = %s FOR UPDATE", (task_id,)).fetchone()
        if task["cancel_requested"]:
            conn.execute("UPDATE fetch_task_items SET status = 'cancelled', finished_at = now() WHERE task_id = %s AND status = 'pending'", (task_id,))
        counts = {row["status"]: row["n"] for row in conn.execute(
            "SELECT status, count(*) AS n FROM fetch_task_items WHERE task_id = %s GROUP BY status", (task_id,)).fetchall()}
        status = final_status(counts, task["cancel_requested"])
        conn.execute("UPDATE fetch_tasks SET status = %s, finished_at = now(), collect_until = NULL WHERE id = %s", (status, task_id))
    return status, counts


def main():
    parser = argparse.ArgumentParser(description="长期资料库抓取任务执行器")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    config = load_config()
    conn = connect(config)
    ensure_schema(conn)
    task = claim_task(conn, args.task_id, args.token)
    if task is None:
        log(f"task {args.task_id} already has a live worker")
        return 0
    options = task["options"]
    log(f"task {args.task_id} worker {os.getpid()} started options={options}")
    stop = threading.Event()
    beat = threading.Thread(target=heartbeat, args=(config, args.task_id, args.token, stop), daemon=True)
    beat.start()
    # 先登记心跳让 CLI 尽快返回，再加载抓取、提取与索引模块
    global fetcher, index, store
    from library import fetcher, index, store
    # 常驻提取进程与 elasticsearch 在后台准备，与第一批网络请求同时进行
    threading.Thread(target=fetcher.EXTRACTORS.warm, daemon=True).start()
    index.preload()
    for content_type in PREPROCESSORS:
        threading.Thread(target=load_preprocessor, args=(content_type,), daemon=True).start()
    db = ConnectionPool(config.pg_dsn, min_size=2, max_size=DB_POOL_SIZE, open=True,
                        kwargs={"row_factory": dict_row, "autocommit": True, "connect_timeout": 10})
    started = time.monotonic()
    indexer = Indexer(db, config)
    try:
        Scheduler(db, config, args.task_id, options, indexer).run()
        # 任务结束前写完全部索引，结束后的本地检索能查到本任务的正文
        indexer.close()
        status, counts = finish_task(conn, args.task_id)
        log(f"task {args.task_id} finished status={status} counts={counts} seconds={time.monotonic() - started:.1f}")
    finally:
        indexer.close()
        stop.set()
        beat.join()
        db.close()
        fetcher.EXTRACTORS.close()
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
