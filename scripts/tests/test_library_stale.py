import os
import sys
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
# UNION_SEARCH_TEST_ENV_FILE 指向演练用资料库的配置，避免测试记录写入日常资料库
load_dotenv(os.environ.get("UNION_SEARCH_TEST_ENV_FILE", ROOT / ".env"), override=False)

from library import fetcher, store  # noqa: E402
from library.archive import document_id  # noqa: E402
from library.config import load_config, missing_env  # noqa: E402
from library.db import FILE_DELETE_LOCK, connect, open_library  # noqa: E402

pytestmark = pytest.mark.skipif(bool(missing_env()), reason="长期资料库未配置")

# 每次请求重定向到不同条目的真实页面，两次抓取得到不同正文
RANDOM_ARTICLE = "https://en.wikipedia.org/wiki/Special:Random"
STABLE_PAGE = "https://example.com/"


@pytest.fixture()
def library():
    config = load_config()
    conn = open_library(config)
    yield config, conn
    conn.close()


def _document(conn, url):
    doc_id = document_id(url)
    with conn.transaction():
        conn.execute("INSERT INTO documents (id, url, fetch_url, domain, title) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (url) DO NOTHING",
                     (doc_id, url, url, urlsplit(url).hostname, url))
    return doc_id


def _fetch(config, url):
    outcome = fetcher.fetch(url, 30)
    assert outcome["status"] == "succeeded", outcome
    return outcome


def _late_older_attempt(config, conn, url):
    """两次真实抓取：先开始的尝试晚于后开始的尝试完成。"""
    doc_id = _document(conn, url)
    older = store.start_attempt(conn, None, doc_id)
    newer = store.start_attempt(conn, None, doc_id)
    assert newer[0] > older[0]
    older_outcome = _fetch(config, url)
    newer_outcome = _fetch(config, url)
    newer_result = store.finish_attempt(conn, config, newer[0], newer[1], doc_id, newer_outcome)
    store.remove_stale_file(conn, config, newer_result[2])
    older_result = store.finish_attempt(conn, config, older[0], older[1], doc_id, older_outcome)
    removal = store.remove_stale_file(conn, config, older_result[2])
    doc = conn.execute("SELECT * FROM documents WHERE id = %s", (doc_id,)).fetchone()
    attempts = {row["id"]: row for row in conn.execute("SELECT * FROM fetch_attempts WHERE id = ANY(%s)", ([older[0], newer[0]],)).fetchall()}
    return doc, attempts, older[0], newer[0], older_result, removal, older_outcome, newer_outcome


def test_late_result_with_different_body_does_not_overwrite(library):
    config, conn = library
    doc, attempts, older_id, newer_id, older_result, removal, older_outcome, newer_outcome = _late_older_attempt(config, conn, RANDOM_ARTICLE)
    assert older_outcome["final_url"] != newer_outcome["final_url"], "两次请求落到同一条目，无法比较不同正文"
    assert older_result[:2] == ("unchanged", "stale")
    assert attempts[older_id]["change_kind"] == "stale"
    assert doc["accepted_attempt_id"] == newer_id
    assert doc["body_hash"] == attempts[newer_id]["body_hash"] != attempts[older_id]["body_hash"]
    # 迟到结果写出的文件被删除，当前正文文件保留
    assert removal == "removed"
    assert not (config.root / older_result[2]).exists()
    assert (config.root / doc["body_path"]).exists()


def test_old_body_file_kept_while_backup_holds_lock(library):
    config, conn = library
    # 用真实页面的正文生成一份旧版本文件，模拟被新正文替换后待删除的文件
    outcome = _fetch(config, STABLE_PAGE)
    relative = f"bodies/zz/test-backup-lock/{uuid.uuid4().hex}.md"
    target = config.root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(outcome["body"], encoding="utf-8")
    backup_conn = connect(config)
    backup_conn.execute("SELECT pg_advisory_lock(%s)", (FILE_DELETE_LOCK,))
    try:
        assert store.remove_stale_file(conn, config, relative) == "deferred"
        assert target.exists()
    finally:
        backup_conn.execute("SELECT pg_advisory_unlock(%s)", (FILE_DELETE_LOCK,))
        backup_conn.close()
    assert store.remove_stale_file(conn, config, relative) == "removed"
    assert not target.exists()


def test_late_result_with_same_body_is_stale(library):
    config, conn = library
    doc, attempts, older_id, newer_id, older_result, removal, _, _ = _late_older_attempt(config, conn, STABLE_PAGE)
    assert older_result == ("unchanged", "stale", None)
    assert removal is None
    assert doc["accepted_attempt_id"] == newer_id
    assert (config.root / doc["body_path"]).exists()
