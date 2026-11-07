from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

SCHEMA_VERSION = 3
SCHEMA_FILE = Path(__file__).with_name("schema.sql")
# 正文文件删除与备份互斥：删除方取共享锁，备份全程持有排他锁
FILE_DELETE_LOCK = 4207115


def connect(config):
    # 自动提交模式下，每个 conn.transaction() 块都是独立的真实事务；单条查询不会留下未提交的隐式事务
    # 连接超时 10 秒，数据库不可用时尽快明确失败
    return psycopg.connect(config.pg_dsn, row_factory=dict_row, autocommit=True, connect_timeout=10)


def ensure_schema(conn) -> int:
    # 结构已是当前版本时不执行 DDL；DDL 的表锁会与执行中的抓取写入互相等待
    if conn.execute("SELECT to_regclass('schema_meta') AS name").fetchone()["name"]:
        current = conn.execute("SELECT max(version) AS version FROM schema_meta").fetchone()["version"]
        if current == SCHEMA_VERSION:
            return current
    with conn.transaction():
        # 多个进程同时首次运行时，用 advisory lock 串行建表与升级
        conn.execute("SELECT pg_advisory_xact_lock(4207114)")
        exists = conn.execute("SELECT to_regclass('schema_meta') AS name").fetchone()["name"]
        current = conn.execute("SELECT max(version) AS version FROM schema_meta").fetchone()["version"] if exists else None
        if current is None:
            conn.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_meta (version) VALUES (%s)", (SCHEMA_VERSION,))
            return SCHEMA_VERSION
        if current > SCHEMA_VERSION:
            raise RuntimeError(f"资料库结构版本为 {current}，高于当前代码的版本 {SCHEMA_VERSION}")
        for version in range(current + 1, SCHEMA_VERSION + 1):
            MIGRATIONS[version](conn)
            conn.execute("INSERT INTO schema_meta (version) VALUES (%s)", (version,))
        return SCHEMA_VERSION


def _migrate_fetch_url(conn):
    """版本 2：资料增加实际请求地址。按最早一次命中的渠道原始字段还原；没有原始字段的旧导入命中只有规范地址。"""
    from union_search.structured_results import source_page_url

    conn.execute("ALTER TABLE documents ADD COLUMN fetch_url text")
    rows = conn.execute("""SELECT DISTINCT ON (h.document_id) h.document_id, h.raw, d.url
                           FROM documents d JOIN search_hits h ON h.document_id = d.id JOIN search_runs r ON r.id = h.search_id
                           ORDER BY h.document_id, (h.raw IS NULL), r.started_at, h.platform, h.rank""").fetchall()
    for row in rows:
        conn.execute("UPDATE documents SET fetch_url = %s WHERE id = %s",
                     (source_page_url(row["raw"]) if row["raw"] else row["url"], row["document_id"]))
    conn.execute("UPDATE documents SET fetch_url = url WHERE fetch_url IS NULL")
    conn.execute("ALTER TABLE documents ALTER COLUMN fetch_url SET NOT NULL")
    conn.execute("UPDATE documents SET index_state = 'pending'")


def _migrate_collect_until(conn):
    # 版本 3：搜索进行中即开始抓取，任务在收集截止前持续接收新任务项
    conn.execute("ALTER TABLE fetch_tasks ADD COLUMN collect_until timestamptz")


MIGRATIONS = {2: _migrate_fetch_url, 3: _migrate_collect_until}


def open_library(config):
    conn = connect(config)
    ensure_schema(conn)
    return conn


def jsonb(value):
    return Jsonb(value)


@contextmanager
def file_delete_guard(conn):
    """删除正文文件前进入。备份进行中时得到 False，调用方保留文件，备份结束后由 library repair 清理。"""
    granted = conn.execute("SELECT pg_try_advisory_lock_shared(%s) AS ok", (FILE_DELETE_LOCK,)).fetchone()["ok"]
    try:
        yield granted
    finally:
        if granted:
            conn.execute("SELECT pg_advisory_unlock_shared(%s)", (FILE_DELETE_LOCK,))
