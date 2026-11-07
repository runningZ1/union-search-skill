import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from psycopg.conninfo import conninfo_to_dict

from library import index
from library.compare import body_hash
from library.db import FILE_DELETE_LOCK, SCHEMA_VERSION, connect, ensure_schema

BACKUP_FORMAT = 1
DUMP_FILE = "database.dump"
MANIFEST_FILE = "manifest.json"
TABLES = ("search_runs", "search_channels", "documents", "search_hits", "fetch_tasks", "fetch_task_items", "fetch_attempts")
# DSN 参数到 libpq 环境变量的映射；密码经环境变量传给 pg_dump/pg_restore，不出现在命令行
PG_ENV = {"host": "PGHOST", "port": "PGPORT", "user": "PGUSER", "password": "PGPASSWORD", "dbname": "PGDATABASE",
          "sslmode": "PGSSLMODE", "connect_timeout": "PGCONNECT_TIMEOUT"}


class BackupInvalid(ValueError):
    pass


class RestoreTargetNotEmpty(RuntimeError):
    pass


class LibraryCorrupted(RuntimeError):
    pass


class MissingTool(RuntimeError):
    pass


def pg_tool_status():
    return {name: shutil.which(name) for name in ("pg_dump", "pg_restore")}


def _tool(name):
    path = shutil.which(name)
    if path is None:
        raise MissingTool(f"{name} 不在 PATH 中，把 PostgreSQL 的 bin 目录加入 PATH")
    return path


def _pg_env(config):
    params = conninfo_to_dict(config.pg_dsn)
    unsupported = sorted(set(params) - set(PG_ENV))
    if unsupported:
        raise ValueError(f"UNION_SEARCH_PG_DSN 含备份工具未映射的参数: {unsupported}")
    env = dict(os.environ)
    for key, value in params.items():
        env[PG_ENV[key]] = str(value)
    return env, params["dbname"]


def _run(command, env):
    # 不弹出控制台窗口
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    completed = subprocess.run(command, env=env, capture_output=True, creationflags=flags)
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace")[-4000:]
        raise RuntimeError(f"{Path(command[0]).name} 退出码 {completed.returncode}: {stderr}")


def _file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _counts(conn):
    return {table: conn.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"] for table in TABLES}


def _copy_body(source_root, target_root, row):
    """复制一份正文并核对内容哈希；哈希不符说明源文件已损坏。"""
    source = source_root / row["body_path"]
    if not source.exists():
        raise LibraryCorrupted(f"资料 {row['id']} 的正文文件缺失: {source}")
    if body_hash(source.read_text(encoding="utf-8")) != row["body_hash"]:
        raise LibraryCorrupted(f"资料 {row['id']} 的正文文件内容与记录的哈希不符: {source}")
    target = target_root / row["body_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target.stat().st_size


def create_backup(config, output: Path):
    """数据库与正文文件来自同一时刻：导出快照的事务内列出正文文件，pg_dump 使用同一快照。
    备份全程持有正文删除锁，快照引用的旧正文文件在复制完成前不会被删除。"""
    pg_dump = _tool("pg_dump")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"备份目录非空: {output}")
    output.mkdir(parents=True, exist_ok=True)
    env, _ = _pg_env(config)
    started = datetime.now(timezone.utc)
    lock_conn = connect(config)
    ensure_schema(lock_conn)
    # 等待进行中的删除完成；之后新的删除请求会把文件留给 library repair
    lock_conn.execute("SELECT pg_advisory_lock(%s)", (FILE_DELETE_LOCK,))
    try:
        snap_conn = connect(config)
        with snap_conn.transaction():
            snap_conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            snapshot = snap_conn.execute("SELECT pg_export_snapshot() AS id").fetchone()["id"]
            counts = _counts(snap_conn)
            bodies = snap_conn.execute("SELECT id, body_path, body_hash FROM documents WHERE body_path IS NOT NULL ORDER BY id").fetchall()
            _run([pg_dump, "--format=custom", "--no-owner", "--no-privileges", f"--snapshot={snapshot}",
                  f"--file={output / DUMP_FILE}"], env)
        snap_conn.close()
        body_bytes = sum(_copy_body(config.root, output, row) for row in bodies)
    finally:
        lock_conn.execute("SELECT pg_advisory_unlock(%s)", (FILE_DELETE_LOCK,))
        lock_conn.close()
    manifest = {
        "format": BACKUP_FORMAT,
        "schema_version": SCHEMA_VERSION,
        "created_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "source": config.public(),
        "counts": counts,
        "database_dump": {"file": DUMP_FILE, "sha256": _file_sha256(output / DUMP_FILE), "bytes": (output / DUMP_FILE).stat().st_size},
        "bodies": {"files": len(bodies), "bytes": body_bytes,
                   "items": [{"document_id": row["id"], "path": row["body_path"], "hash": row["body_hash"]} for row in bodies]},
    }
    (output / MANIFEST_FILE).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {key: manifest[key] for key in ("format", "schema_version", "created_at", "finished_at", "source", "counts", "database_dump")} | {
        "bodies": {"files": len(bodies), "bytes": body_bytes}, "output": str(output)}


def _load_manifest(source: Path):
    path = source / MANIFEST_FILE
    if not path.exists():
        raise BackupInvalid(f"备份目录缺少 {MANIFEST_FILE}: {source}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not (source / manifest["database_dump"]["file"]).exists():
        raise BackupInvalid(f"备份目录缺少数据库导出文件: {source / manifest['database_dump']['file']}")
    if manifest["format"] != BACKUP_FORMAT:
        raise BackupInvalid(f"备份格式 {manifest['format']} 与当前代码的格式 {BACKUP_FORMAT} 不同")
    # 旧版本备份恢复后由 ensure_schema 升级；更新版本的备份需要更新代码
    if manifest["schema_version"] > SCHEMA_VERSION:
        raise BackupInvalid(f"备份的资料库结构版本 {manifest['schema_version']} 高于当前代码的版本 {SCHEMA_VERSION}")
    dump = source / manifest["database_dump"]["file"]
    if _file_sha256(dump) != manifest["database_dump"]["sha256"]:
        raise BackupInvalid(f"数据库导出文件的哈希与清单不符: {dump}")
    return manifest


def _ensure_empty_target(conn, config):
    tables = conn.execute("SELECT count(*) AS n FROM pg_tables WHERE schemaname = 'public'").fetchone()["n"]
    if tables:
        raise RestoreTargetNotEmpty(f"目标数据库已有 {tables} 张表，恢复只写入空数据库")
    if any(config.bodies_dir.iterdir()):
        raise RestoreTargetNotEmpty(f"目标正文目录非空: {config.bodies_dir}")
    if index.client(config).indices.exists(index=config.es_index):
        raise RestoreTargetNotEmpty(f"目标检索索引已存在: {config.es_index}")


def restore_backup(config, source: Path):
    """恢复到当前配置指向的空数据库、空资料库目录和不存在的索引；索引由归档重建。"""
    pg_restore = _tool("pg_restore")
    manifest = _load_manifest(source)
    env, dbname = _pg_env(config)
    conn = connect(config)
    _ensure_empty_target(conn, config)
    _run([pg_restore, "--no-owner", "--no-privileges", "--exit-on-error", "--single-transaction", f"--dbname={dbname}",
          str(source / manifest["database_dump"]["file"])], env)
    ensure_schema(conn)
    counts = _counts(conn)
    if counts != manifest["counts"]:
        raise LibraryCorrupted(f"恢复后的记录数与备份清单不符: 恢复 {counts}，清单 {manifest['counts']}")
    bodies = conn.execute("SELECT id, body_path, body_hash FROM documents WHERE body_path IS NOT NULL ORDER BY id").fetchall()
    listed = {(item["document_id"], item["path"], item["hash"]) for item in manifest["bodies"]["items"]}
    if {(row["id"], row["body_path"], row["body_hash"]) for row in bodies} != listed:
        raise LibraryCorrupted("恢复后的正文引用与备份清单不符")
    body_bytes = sum(_copy_body(source, config.root, row) for row in bodies)
    with conn.transaction():
        conn.execute("UPDATE documents SET index_state = 'pending', index_error = NULL, indexed_at = NULL")
    ids = [row["id"] for row in conn.execute("SELECT id FROM documents ORDER BY id").fetchall()]
    indexed = {"indexed": 0, "failed": 0, "errors": []}
    for start in range(0, len(ids), 200):
        result = index.sync_documents(conn, config, ids[start:start + 200], refresh=True)
        indexed["indexed"] += result["indexed"]
        indexed["failed"] += result["failed"]
        if result["error"]:
            indexed["errors"].append(result["error"])
    conn.close()
    return {"source": str(source), "backup_created_at": manifest["created_at"], "target": config.public(), "counts": counts,
            "bodies": {"files": len(bodies), "bytes": body_bytes}, "index": indexed}
