-- 长期资料库结构；版本号见 db.py 的 SCHEMA_VERSION
CREATE TABLE IF NOT EXISTS schema_meta (
    version integer PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

-- 一次搜索运行：关键词、渠道、参数和完整搜索快照
CREATE TABLE IF NOT EXISTS search_runs (
    id text PRIMARY KEY,
    command text NOT NULL,
    query text,
    params jsonb NOT NULL,
    started_at timestamptz NOT NULL,
    archived_at timestamptz NOT NULL DEFAULT now(),
    search_ok boolean NOT NULL,
    raw_total integer NOT NULL,
    unique_total integer NOT NULL,
    snapshot jsonb NOT NULL,
    import_source text UNIQUE,
    legacy_request_id text
);

-- 每个渠道在这次运行中的状态，失败和零结果都保留
CREATE TABLE IF NOT EXISTS search_channels (
    search_id text NOT NULL REFERENCES search_runs(id),
    platform text NOT NULL,
    status text NOT NULL,
    item_count integer NOT NULL,
    duration_ms integer,
    error jsonb,
    warning text,
    PRIMARY KEY (search_id, platform)
);

-- 资料：按规范化网址稳定标识，可关联多次搜索命中
CREATE TABLE IF NOT EXISTS documents (
    id text PRIMARY KEY,
    -- url 是去重用的规范地址，fetch_url 是首次命中时渠道给出、实际请求的页面地址
    url text NOT NULL UNIQUE,
    fetch_url text NOT NULL,
    domain text NOT NULL,
    title text NOT NULL,
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    content_type text NOT NULL DEFAULT 'unknown',
    content_type_evidence jsonb NOT NULL DEFAULT '[]',
    restrictions jsonb NOT NULL DEFAULT '[]',
    metadata jsonb NOT NULL DEFAULT '{}',
    body_hash text,
    body_path text,
    body_chars integer,
    body_extractor text,
    body_accepted_at timestamptz,
    body_checked_at timestamptz,
    body_etag text,
    body_last_modified text,
    accepted_attempt_id bigint,
    last_attempt_id bigint,
    last_attempt_status text,
    preprocess_state text,
    index_state text NOT NULL DEFAULT 'pending',
    index_error text,
    indexed_at timestamptz
);
CREATE INDEX IF NOT EXISTS documents_index_state ON documents (index_state);

-- 搜索命中：渠道返回的一条结果及其完整摘要与原始字段
CREATE TABLE IF NOT EXISTS search_hits (
    search_id text NOT NULL REFERENCES search_runs(id),
    platform text NOT NULL,
    rank integer NOT NULL,
    display_id integer,
    document_id text NOT NULL REFERENCES documents(id),
    title text NOT NULL,
    url text NOT NULL,
    content text NOT NULL,
    published text,
    thumbnail text,
    engine text,
    raw jsonb,
    PRIMARY KEY (search_id, platform, rank)
);
CREATE INDEX IF NOT EXISTS search_hits_document ON search_hits (document_id);
CREATE INDEX IF NOT EXISTS search_hits_display ON search_hits (search_id, display_id);

CREATE TABLE IF NOT EXISTS fetch_tasks (
    id text PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    search_id text REFERENCES search_runs(id),
    scope text NOT NULL,
    selection jsonb NOT NULL,
    options jsonb NOT NULL,
    status text NOT NULL,
    cancel_requested boolean NOT NULL DEFAULT false,
    worker_pid integer,
    worker_token text,
    worker_heartbeat timestamptz,
    worker_started_at timestamptz,
    finished_at timestamptz,
    -- 不为空时任务仍在收集：搜索进行中逐个渠道追加任务项，执行器在截止前持续等待
    collect_until timestamptz
);

CREATE TABLE IF NOT EXISTS fetch_task_items (
    task_id text NOT NULL REFERENCES fetch_tasks(id),
    seq integer NOT NULL,
    document_id text NOT NULL REFERENCES documents(id),
    url text NOT NULL,
    status text NOT NULL DEFAULT 'pending',
    attempt_id bigint,
    started_at timestamptz,
    finished_at timestamptz,
    error text,
    PRIMARY KEY (task_id, seq),
    UNIQUE (task_id, document_id)
);
CREATE INDEX IF NOT EXISTS fetch_task_items_status ON fetch_task_items (task_id, status);

-- 每次抓取尝试的结果；正文只保留资料的当前版本，尝试记录保留哈希和变化类别
CREATE TABLE IF NOT EXISTS fetch_attempts (
    id bigserial PRIMARY KEY,
    task_id text REFERENCES fetch_tasks(id),
    document_id text NOT NULL REFERENCES documents(id),
    started_at timestamptz NOT NULL,
    finished_at timestamptz,
    duration_ms integer,
    status text NOT NULL,
    http_status integer,
    final_url text,
    response_type text,
    content_type text,
    restrictions jsonb NOT NULL DEFAULT '[]',
    technical_reason text,
    evidence jsonb NOT NULL DEFAULT '[]',
    extractor text,
    body_hash text,
    previous_hash text,
    change_kind text,
    diff_stats jsonb,
    similarity double precision,
    partial_body text,
    error text
);
CREATE INDEX IF NOT EXISTS fetch_attempts_document ON fetch_attempts (document_id, id);
