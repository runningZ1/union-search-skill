import importlib
import logging
import threading
from datetime import datetime, timezone

# 每个 HTTP 请求的 INFO 日志会淹没 stderr 诊断信息
logging.getLogger("elastic_transport").setLevel(logging.WARNING)

# cjk 分析器对中文做二元切分，英文与数字按标准分词并转小写；不依赖额外插件。
# 标准分词会丢掉 % 等单位符号，units 子字段把“数字+单位”整体作为词，查询含单位时要求精确命中。
UNIT_PATTERN = (r"\d+(?:[.,]\d+)?\s*(?:%|％|‰|g/m2|g/m²|gsm|dtex|tex|kg|mm|cm|g(?![a-z])|m(?![a-z])|d(?![a-z])"
                r"|旦|支|克|公斤|毫米|厘米|米|元|万|亿|℃|°c)")
ANALYSIS = {
    "char_filter": {"fullwidth_percent": {"type": "mapping", "mappings": ["％ => %"]}},
    "tokenizer": {"number_unit": {"type": "pattern", "pattern": UNIT_PATTERN, "group": 0, "flags": "CASE_INSENSITIVE"}},
    "filter": {"strip_spaces": {"type": "pattern_replace", "pattern": r"\s+", "replacement": ""}},
    "analyzer": {"number_unit": {"type": "custom", "char_filter": ["fullwidth_percent"], "tokenizer": "number_unit",
                                 "filter": ["lowercase", "strip_spaces"]}},
}
UNITS = {"units": {"type": "text", "analyzer": "number_unit"}}
TEXT = {"type": "text", "analyzer": "cjk", "fields": UNITS}
MAPPING = {
    "properties": {
        "document_id": {"type": "keyword"},
        "url": {"type": "keyword"},
        "domain": {"type": "keyword"},
        "title": {"type": "text", "analyzer": "cjk", "fields": {"raw": {"type": "keyword", "ignore_above": 1024}, **UNITS}},
        "summaries": TEXT,
        "body": TEXT,
        "queries": TEXT,
        "platforms": {"type": "keyword"},
        "content_type": {"type": "keyword"},
        "restrictions": {"type": "keyword"},
        "fetch_status": {"type": "keyword"},
        "has_body": {"type": "boolean"},
        "body_chars": {"type": "integer"},
        "first_seen_at": {"type": "date"},
        "last_seen_at": {"type": "date"},
        "body_accepted_at": {"type": "date"},
        "body_checked_at": {"type": "date"},
    }
}
SEARCH_FIELDS = ["title^3", "summaries^2", "body", "queries"]
HIGHLIGHT_FIELDS = ("title", "summaries", "body")
# Elasticsearch 默认 index.highlight.max_analyzed_offset 为 1000000，请求值必须小于它
HIGHLIGHT_MAX_ANALYZED_OFFSET = 999_999


_clients = {}
_clients_lock = threading.Lock()


def preload():
    # 导入 elasticsearch 需要 1 秒以上；在搜索或首批抓取进行时由后台线程导入，用到时不再等待。
    # 后台导入失败时，client() 中的导入会再次抛出同一错误
    threading.Thread(target=importlib.import_module, args=("elasticsearch.helpers",), daemon=True).start()


def client(config):
    # 同一进程复用一个客户端及其连接池；客户端本身线程安全，执行器的各线程共用
    from elasticsearch import Elasticsearch

    key = (config.es_url, config.es_api_key)
    with _clients_lock:
        if key not in _clients:
            _clients[key] = Elasticsearch(config.es_url, api_key=config.es_api_key, request_timeout=30)
        return _clients[key]


def ensure_index(es, name):
    if not es.indices.exists(index=name):
        es.indices.create(index=name, mappings=MAPPING, settings={"number_of_replicas": 0, "analysis": ANALYSIS})


def _iso(value):
    return value.isoformat() if value else None


def build_document(conn, config, document_id):
    doc = conn.execute("SELECT * FROM documents WHERE id = %s", (document_id,)).fetchone()
    hits = conn.execute(
        """SELECT DISTINCT h.content, h.platform, r.query FROM search_hits h JOIN search_runs r ON r.id = h.search_id
           WHERE h.document_id = %s""", (document_id,)).fetchall()
    body = (config.root / doc["body_path"]).read_text(encoding="utf-8") if doc["body_path"] else None
    return {
        "document_id": doc["id"],
        "url": doc["fetch_url"],
        "domain": doc["domain"],
        "title": doc["title"],
        "summaries": sorted({row["content"] for row in hits if row["content"]}),
        "body": body,
        "queries": sorted({row["query"] for row in hits if row["query"]}),
        "platforms": sorted({row["platform"] for row in hits}),
        "content_type": doc["content_type"],
        "restrictions": sorted({item["kind"] for item in doc["restrictions"]}),
        "fetch_status": doc["last_attempt_status"] or "not_fetched",
        "has_body": body is not None,
        "body_chars": doc["body_chars"],
        "first_seen_at": _iso(doc["first_seen_at"]),
        "last_seen_at": _iso(doc["last_seen_at"]),
        "body_accepted_at": _iso(doc["body_accepted_at"]),
        "body_checked_at": _iso(doc["body_checked_at"]),
    }


def sync_documents(conn, config, document_ids, refresh=False):
    """把资料写入检索索引。索引失败只记录在资料上，已归档内容不受影响。
    默认不等待索引刷新（ES 每秒自动刷新）；重建索引时等待刷新后再返回。"""
    from elasticsearch import helpers

    if not document_ids:
        return {"indexed": 0, "failed": 0, "error": None}
    es = client(config)
    try:
        ensure_index(es, config.es_index)
        actions = [{"_index": config.es_index,"_id": doc_id, "_source": build_document(conn, config, doc_id)} for doc_id in document_ids]
        _, failures = helpers.bulk(es, actions, raise_on_error=False, refresh="wait_for" if refresh else False)
    except Exception as exc:  # 索引服务的任何故障都转为待修复状态，由 library reindex 恢复
        with conn.transaction():
            conn.execute("UPDATE documents SET index_state = 'failed', index_error = %s WHERE id = ANY(%s)",
                         (f"{type(exc).__name__}: {exc}"[:2000], list(document_ids)))
        return {"indexed": 0, "failed": len(document_ids), "error": f"{type(exc).__name__}: {exc}"}
    failed = {item["index"]["_id"]: str(item["index"].get("error")) for item in failures}
    now = datetime.now(timezone.utc)
    with conn.transaction():
        for doc_id in document_ids:
            if doc_id in failed:
                conn.execute("UPDATE documents SET index_state = 'failed', index_error = %s WHERE id = %s", (failed[doc_id][:2000], doc_id))
            else:
                conn.execute("UPDATE documents SET index_state = 'indexed', index_error = NULL, indexed_at = %s WHERE id = %s", (now, doc_id))
    return {"indexed": len(document_ids) - len(failed), "failed": len(failed), "error": next(iter(failed.values()), None)}


def search(config, query, filters, limit):
    """本地资料库检索；limit 为 None 时用 search_after 取全部命中。"""
    es = client(config)
    if not es.indices.exists(index=config.es_index):
        raise LookupError(f"检索索引 {config.es_index} 不存在，先运行 library reindex --all")
    must = [{"multi_match": {"query": query, "fields": SEARCH_FIELDS, "type": "cross_fields", "operator": "and"}}]
    # 用索引自己的单位分析器解析查询；含“数字+单位”时要求原样出现，避免 100% 退化成只匹配 100
    units = [token["token"] for token in es.indices.analyze(index=config.es_index,analyzer="number_unit", text=query)["tokens"]]
    for unit in units:
        must.append({"multi_match": {"query": unit, "fields": [field + ".units" for field in ("title", "summaries", "body")]}})
    should = [{"match_phrase": {field: {"query": query, "boost": 2}}} for field in ("title", "summaries", "body")]
    body = {
        "query": {"bool": {"must": must, "should": should, "filter": filters}},
        # 超长正文只在前一百万字符内取高亮片段（索引设置 index.highlight.max_analyzed_offset 的上限）；命中判断仍使用全文
        "highlight": {"max_analyzed_offset": HIGHLIGHT_MAX_ANALYZED_OFFSET,
                      "fields": {field: {"fragment_size": 160, "number_of_fragments": 3} for field in HIGHLIGHT_FIELDS}},
        "sort": [{"_score": "desc"}, {"document_id": "asc"}],
        "_source": {"excludes": ["body"]},
        "track_total_hits": True,
    }
    rows = []
    total = None
    search_after = None
    while True:
        size = 500 if limit is None else min(500, limit - len(rows))
        if size <= 0:
            break
        response = es.search(index=config.es_index,size=size, search_after=search_after, **body)
        total = response["hits"]["total"]["value"]
        page = response["hits"]["hits"]
        rows.extend(page)
        if len(page) < size:
            break
        search_after = page[-1]["sort"]
    return total, rows
