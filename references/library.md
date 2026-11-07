# 长期资料库操作说明

搜索、抓取、读取是三个独立步骤。搜索只归档命中；抓取必须显式发起；读取和本地检索不访问网络。实现细节见 [资料库模块](../scripts/library/README.md)。

## 配置

在 `.env` 中设置以下变量，用 `doctor` 检查目录、PostgreSQL 与 Elasticsearch：

| 变量 | 含义 |
|------|------|
| `UNION_SEARCH_LIBRARY_DIR` | 资料库目录（绝对路径），保存正文、日志和暂存文件 |
| `UNION_SEARCH_PG_DSN` | PostgreSQL 连接串，首次使用时自动建表 |
| `UNION_SEARCH_ES_URL` | Elasticsearch 地址 |
| `UNION_SEARCH_ES_API_KEY` | 可读写该索引的 API Key |
| `UNION_SEARCH_ES_INDEX` | 检索索引名，例如 `union_search_documents`；不存在时自动创建 |

依赖已在 `requirements.txt` 中：`psycopg[binary]`、`psycopg-pool`、`elasticsearch`、`beautifulsoup4`、`pymupdf4llm`。抓取网页还需要 Defuddle 运行时，安装步骤见 [提取引擎](../scripts/url_to_markdown/README.md)。备份与恢复需要 PostgreSQL 客户端工具 `pg_dump`、`pg_restore` 在 `PATH` 中（Windows 默认位于 `C:\Program Files\PostgreSQL\<版本>\bin`），`doctor` 的 `library_backup_tools` 项会检查。

未配置时搜索照常返回结果，`meta.library.archived` 为 `false` 并说明缺少的变量；带 `--fetch all` 时返回 `LIBRARY_NOT_CONFIGURED`，不创建任务。

## 搜索归档

`search`、`platform` 和直接渠道命令每次都把全部命中、渠道状态（含失败与零结果）和完整摘要写入资料库。`--content none` 只隐藏展示，不影响归档。归档结果在 `meta.library`：

- `archived`、`search_id`、`hits`（渠道命中数）、`unique_results`、`documents`、`index`、`timing_ms`（`archive`、`index`）。
- 带 `--fetch all` 时，抓取任务在搜索开始前创建，每个渠道返回后立即开始抓取它的结果，不等其他渠道；搜索返回时通常已有正文可读。`meta.fetch_task` 返回任务 ID 与执行器状态。
- 归档失败时顶层 `ok` 为 `false`，错误码 `ARCHIVE_FAILURE`，退出码 `3`；`data` 仍是本次搜索结果，`meta.library.available_results` 指向 `.work` 中的完整结果文件。附带的抓取不会启动。

```bash
python union_search_cli.py search "女装 再生面料 廓形 工艺" --group api -o .work/search.json
python union_search_cli.py search "女装 再生面料 廓形 工艺" --group api --fetch all -o .work/search.json
```

## 抓取

```bash
python union_search_cli.py fetch --search-id <search_id> --ids 1 3
python union_search_cli.py fetch --search-id <search_id> --all
python union_search_cli.py fetch --document-ids <document_id> [<document_id> ...]
python union_search_cli.py fetch --search-id <search_id> --ids 1 --wait --wait-timeout 120
```

- `--ids` 是该搜索运行展示的结果 ID（`final_items[].id`，单渠道为 `items[].id`），只在该运行内有效。任一 ID 无效时返回 `UNKNOWN_ID`，不创建任务。
- `--all` 覆盖该运行的全部唯一网址，不按相关性筛选。PDF 下载后按文字层转为 Markdown 正文；扫描件没有文字层时记为 `failed`（`no_text_layer`）。视频、播客也创建任务项，记为 `pending_preprocess`，不发起网络请求。
- 命令在任务入库且执行器确认接管后返回 `task_id`，不等待正文。执行器未能启动时返回 `EXECUTOR_START_FAILED`，任务保持 `queued`，可用 `task resume` 重新启动。
- 每次显式抓取都会请求来源并与当前正文比较，即使已有正文。仅搜索再次命中不会抓取。
- 默认并发 32 项、同一主机最多 2 项、单项时限 30 秒（`--fetch-concurrency`、`--fetch-per-host`、`--fetch-timeout`）。时限分别限制网络请求（PDF 为整个下载）和正文提取（PDF 为转换），本机提取排队的时间不计入；超时记为 `failed`（`timeout`）。

## 任务

```bash
python union_search_cli.py task status <task_id>
python union_search_cli.py task wait <task_id> --timeout 300
python union_search_cli.py task resume <task_id>
python union_search_cli.py task retry <task_id> --failed
python union_search_cli.py task cancel <task_id>
python union_search_cli.py task list --limit 20
```

任务状态：`queued`、`running`、`cancelling`、`interrupted`（执行器失联）、`completed`（全部取得正文或未变化）、`partial`、`failed`、`cancelled`。`collecting` 为 `true` 时搜索仍在进行，任务项还会增加。`disposed_items` 是已有结论的项数，`body_success_items` 是取得或确认正文的项数，两者不同。

任务项状态：`pending`、`running`、`succeeded`、`unchanged`、`partial`、`restricted`、`failed`、`pending_preprocess`、`cancelled`。每项附带 `http_status`、`content_type`、`change_kind`（`first`、`unchanged`、`changed`、`not_modified`、`stale`）、`technical_reason`、`restrictions`、`similarity`、`diff_stats` 和 `error`。

`task wait` 在任务未全部取得正文时返回 `ok: false`、`FETCH_INCOMPLETE`、退出码 `4`；仅剩媒体待预处理也属于未全部取得正文。等待超时返回 `TIMEOUT`。

## 读取

```bash
python union_search_cli.py read --document-id <document_id> --body
python union_search_cli.py read --document-id <document_id> --summaries
python union_search_cli.py read --from-file .work/search.json --ids 1 2
```

- 每份资料的 `url` 是抓取时请求的页面地址（首次命中时渠道给出），`canonical_url` 是去重用的规范地址；同一页面的 `www.`、末尾斜杠、跟踪参数写法归为同一资料。
- `--body` 返回完整当前正文、哈希、提取引擎、接受时间和最近检查时间。尚无正文时 `body.state` 为 `not_fetched` 或 `unavailable`，附带抓取命令；受限页面的公开部分在 `body.partial` 中单独给出，不作为正文。
- `--summaries` 返回该资料的全部搜索命中：搜索运行、查询、渠道、排名、完整摘要和渠道原始字段。
- `--from-file` 保持原有含义：读取某次搜索结果文件中的条目。

## 本地检索

```bash
python union_search_cli.py library search "再生涤纶" --has-body
python union_search_cli.py library search "rPET 100%" --content-type article --fetch-status succeeded unchanged
python union_search_cli.py library search "Patagonia 再生" --content none
```

默认返回全部命中，完整显示搜索摘要；`--content none` 隐藏摘要，`--limit` 设置上限。每条结果含资料 ID、来源渠道、类型、限制、获取状态、是否有正文、时间、命中字段和高亮片段；正文用 `read --document-id ... --body` 读取。零结果直接返回，不转为互联网搜索。索引不可用时返回 `INDEX_UNAVAILABLE`，按资料 ID 读取仍然可用。

## 导出

```bash
python union_search_cli.py library export --search-id <search_id> --export-file .work/export.json
python union_search_cli.py library export --search-id <search_id> --task-id <task_id> --export-file .work/export.json
```

把一次搜索写成一个缩进的 UTF-8 JSON 文件，不访问网络。每个搜索渠道是一组，所有组的字段与顺序相同，组内每条结果的字段与顺序也相同，缺失值为 `null`。未指定 `--task-id` 时使用该搜索最近创建的抓取任务；搜索或任务不存在、任务不属于该搜索时返回 `UNKNOWN_ID`。命令信封的 `data` 返回文件路径与 `search` 部分。

```json
{
  "format": "union-search.search-export",
  "version": 2,
  "generated_at": "...",
  "search": {"query": "...", "search_id": "...", "group_count": 23, "result_count": 109, "...": "..."},
  "groups": [
    {
      "group": 1,
      "channel": "duckduckgo",
      "status": "success",
      "result_count": 10,
      "duration_ms": 3875,
      "error_code": null,
      "error_message": null,
      "results": [
        {"index": 1, "title": "...", "url": "...", "content": "...", "published": null, "result_id": 1,
         "document_id": "doc_...", "fetch_status": "succeeded", "fetch_reason": null, "body_file": "D:\\...\\<sha256>.md", "body_chars": 1548}
      ]
    }
  ]
}
```

| 位置 | 字段 |
|------|------|
| `search` | `query`、`search_id`、`started_at`、`ok`、`group_count`（组数，即实际执行的渠道数）、`groups_with_results`、`groups_failed`、`result_count`（全部组的结果条数）、`unique_document_count`（跨渠道去重后的资料数）、`fetch_task_id`、`fetch_task_status`、`fetch_counts`（各抓取结论的项数）、`full_result_file` |
| `groups[]` | `group`（组序号）、`channel`（渠道名）、`status`（`success`、`empty`、`failed`）、`result_count`、`duration_ms`、`error_code`、`error_message`、`results` |
| `groups[].results[]` | `index`（该渠道内的序号，即渠道排名）、`title`、`url`、`content`（完整搜索摘要）、`published`、`result_id`（`fetch --ids` 使用的编号）、`document_id`（`read --document-id` 使用）、`fetch_status`（该任务中的抓取结论；资料不在任务中为 `not_in_task`；没有任务为 `null`）、`fetch_reason`（失败或受限的技术原因）、`body_file`（当前正文 Markdown 的绝对路径）、`body_chars` |

按搜索执行顺序排列各组；失败和零结果的渠道同样成组，`results` 为空数组。同一资料被多个渠道返回时在每组各出现一次。

## 维护

```bash
python union_search_cli.py library status
python union_search_cli.py library reindex
python union_search_cli.py library reindex --all
python union_search_cli.py library import .work/search-results
python union_search_cli.py library repair
python union_search_cli.py library backup --backup-dir D:\backups\library-20261107
python union_search_cli.py library restore --from D:\backups\library-20261107 --env-file <新环境的配置文件>
```

- `status`：资料库位置、各表数量、索引状态和 Elasticsearch 可达性。
- `reindex`：重写未成功入索引的资料；`--all` 删除并按归档重建整个索引，不访问网络。
- `import`：导入旧的 `full.json` 搜索信封（文件或目录），原文件不变。按文件内容哈希识别，同一文件重复导入返回 `already_imported`；实时搜索写入的 `.work` 结果文件也会被识别。返回旧 `request_id` 与新 `search_id` 的对应关系。
- `repair`：核对正文文件与数据库哈希，删除一小时前未被引用的旧正文与暂存文件；正文缺失或不符时返回 `ARCHIVE_FAILURE` 并列出资料 ID。备份进行中时返回 `BACKUP_IN_PROGRESS`，不删除文件。
- `backup`：`--backup-dir` 必须是新目录或空目录。写出数据库导出、全部当前正文和清单，数据库与正文取自同一时刻；抓取任务可以同时运行。返回各表行数、正文文件数与导出文件哈希。
- `restore`：只写入空目标（数据库没有表、正文目录为空、索引不存在），否则返回 `RESTORE_TARGET_NOT_EMPTY`。核对清单、各表行数和每份正文哈希后重建索引；清单或导出文件不符返回 `BACKUP_INVALID`。迁移到新机器时，先按本节配置新环境，再执行 `restore`。

删除搜索运行或资料没有命令入口，取消任务不删除任何已存内容。
