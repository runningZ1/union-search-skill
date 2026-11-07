# 长期资料库

本模块保存全部搜索命中，按需抓取正文，并提供本地检索与读取。CLI 入口是 `search`、`platform` 及直接渠道命令的自动归档，以及 `fetch`、`task`、`read --document-id` 和 `library`。操作步骤见 [资料库操作说明](../../references/library.md)。

## 存储

| 层次 | 位置 | 内容 |
|------|------|------|
| 结构化数据 | PostgreSQL（`UNION_SEARCH_PG_DSN`） | 搜索运行、渠道状态、搜索命中、资料、抓取任务、任务项、抓取尝试 |
| 正文文件 | `<UNION_SEARCH_LIBRARY_DIR>/bodies/<id 前两位>/<document_id>/<sha256>.md` | 每份资料只保留当前正文 |
| 检索索引 | Elasticsearch 索引 `<UNION_SEARCH_ES_INDEX>`（`UNION_SEARCH_ES_URL`、`UNION_SEARCH_ES_API_KEY`） | 标题、全部搜索摘要、正文与状态；可从前两层完整重建 |
| 执行日志 | `<UNION_SEARCH_LIBRARY_DIR>/logs/<task_id>.log` | 后台执行器逐项记录 |

`.work/search-results/` 仍保存每次搜索的完整信封，供 `read --from-file` 使用，长期保存以资料库为准。

## 备份与恢复

`library backup --backup-dir <目录>` 生成 `database.dump`（`pg_dump` 自定义格式）、`bodies/`（当前正文文件）和 `manifest.json`（各表行数、导出文件哈希、每份正文的路径与哈希）。检索索引不备份，恢复时重建。

数据库与正文文件取自同一时刻：备份在可重复读的只读事务中导出快照，在同一事务内列出正文文件，`pg_dump --snapshot` 使用这个快照。备份全程持有正文删除锁（PostgreSQL advisory lock）；执行器替换正文后删除旧文件、`library repair` 清理文件前都要取得该锁，备份进行中时旧文件保留（执行日志记为 `old_file=deferred`），`repair` 返回 `BACKUP_IN_PROGRESS`。执行中的抓取任务不因备份暂停。复制正文时逐份核对哈希，不符时中止备份。

旧结构版本的备份可以恢复，导入后自动升级到当前版本；更高版本的备份返回 `BACKUP_INVALID`。`library restore --from <目录>` 写入当前配置指向的目标：数据库没有任何表、`bodies/` 为空、索引不存在，否则返回 `RESTORE_TARGET_NOT_EMPTY`。恢复依次核对清单与导出文件哈希、用 `pg_restore --single-transaction` 导入、核对各表行数与正文引用、逐份复制并核对正文，最后按归档重建索引。`pg_dump` 与 `pg_restore` 需在 `PATH` 中，主版本不低于服务器；连接参数经 libpq 环境变量传入，密码不出现在命令行。

## 数据层次

- `search_runs.snapshot`：本次 CLI 完整信封（含渠道原始字段），键名包含 key、token、secret、password、cookie、authorization 的字段不入库。
- `search_hits`：每个渠道返回的每一条结果，含完整摘要、排名、展示 ID 和渠道原始字段 `raw`。同一网址跨渠道分别保留。
- `documents`：按规范网址（去掉 `www.`、末尾斜杠和跟踪参数，见 `union_search/structured_results.py` 的 `canonical_url`）生成稳定 ID（`doc_` + 规范网址 SHA-256 前 20 位），`url` 列保存规范网址。`fetch_url` 是首次命中时渠道给出的页面地址，抓取请求使用它；不少网站只在 `www.` 主机上提供 HTTPS。结构版本 2 起新增该列，升级时从各资料最早一次命中的渠道原始字段还原。记录内容类型及依据、访问限制、元数据、当前正文指针与哈希、最近一次尝试状态和索引状态。
- `fetch_attempts`：每次抓取的 HTTP 状态、最终地址、类型、限制、技术原因、依据、正文哈希、更新前哈希、变化类别、逐行统计、变化片段和相似度。受限页面的公开部分保存在 `partial_body`。

渠道原始字段只保存适配器实际收到的业务字段，不包含 HTTP 请求头或已被适配器丢弃的数据。

## 抓取判定

执行器用 `curl_cffi` 请求页面（每个执行线程复用一个会话），按响应头、页面声明和内容检测字符集，再交给常驻的 Defuddle 提取进程（`url_to_markdown/engines/defuddle-node/extract_html.mjs`）以真实页面地址提取 Markdown。单项时限分别限制网络请求和提取运算，等待空闲提取进程的时间不计入。

| 结论 | 条件 |
|------|------|
| `pending_preprocess` | 渠道或网址表明是视频、播客，或响应类型为视频、音频，且没有注册预处理模块；不发起网络请求或只读取响应头 |
| `restricted` | 识别到访问限制，且文字少于 200 字或状态码为 401、403、451 |
| `partial` | 明确限制下取得的公开部分；疑似限制且短于现有正文一半；或正文短于该资料最长搜索摘要的 80%（软 404、错误页、提取不全） |
| `failed` | 网络错误、超时、限流、服务器错误、状态码 200 的程序错误页（PHP `Fatal error` / `Parse error` 输出，`server_error_page`）、需要 JS 渲染、空提取、类型不支持等技术原因 |
| `succeeded` / `unchanged` | 取得有效正文；与当前正文哈希相同或来源返回 304 时为 `unchanged` |

访问限制依据：HTTP 401、402、403、451；人机验证元素（reCAPTCHA、hCaptcha、Turnstile、Cloudflare 质询、DataDome、PerimeterX、极验）；结构化数据 `isAccessibleForFree=false` 或 `article:content_tier`；完整 class 或 id 为付费墙容器名；短正文页面上的密码表单；跳转到登录路径。识别到人机验证时，401/403 推断的登录或权限限制降为疑似。正文中出现“付费”“登录”等词不作为依据。

## 正文比较与覆盖

比较前只统一换行、去掉行尾空格并压缩连续空行。规范化正文的 SHA-256 相同则不写新文件，只更新检查时间；不同则写入新的哈希文件，在数据库事务中切换指针，提交后删除旧文件。相似度和逐行统计只用于诊断，任何增删改都会覆盖。`diff_stats.changes` 保存最多 20 处变化附近的片段（每处 300 字以内），用于核对数字修改，不保存旧全文。

尝试 ID 按开始先后递增。资料已接受更晚开始的尝试时，较早尝试的迟到结果记为 `stale`，不覆盖，迟到结果写出的文件随即删除。失败、受限、部分内容都不改动当前正文。

已有正文由当前提取引擎生成时，请求带 `If-None-Match` / `If-Modified-Since`，来源返回 304 记为 `not_modified`。提取引擎或其版本变化后不发条件请求，重新取得内容并转换，差异中记录 `diff_stats.extractor_changed`。

## 任务执行

`fetch` 先在数据库中创建任务和任务项，再启动独立执行器进程（Windows 使用不可见控制台并脱离父进程作业），等待执行器写入心跳后返回任务 ID。执行器每 5 秒写一次心跳，超过 30 秒无心跳的运行中任务显示为 `interrupted`。

`search --fetch all` 在搜索开始前创建任务并启动执行器，任务处于收集状态（`fetch_tasks.collect_until`，`task status` 的 `collecting` 为 `true`）。每个渠道返回后，它的结果立即登记为资料并追加为任务项，执行器随即开始抓取，不等其他渠道。归档完成后补齐全部资料、关联搜索运行并结束收集。搜索或归档中途失败时结束收集并取消任务，已取得的正文保留；CLI 被强制终止时，执行器在收集截止时间（搜索时限加 120 秒）后按已收到的项完成任务。

执行器结构：

- 单线程调度器从数据库读取待执行项，按任务并发上限与同一主机上限派发给执行线程；同一主机已满时先派发其他主机的项。
- 执行线程只在读写数据库的短时间内从连接池（最多 16 个连接）借用连接，网络请求与提取期间不占用。
- 提取进程数为 CPU 核数的一半，进程常驻，JSDOM 与 Defuddle 只在启动时加载一次。实测 14 核机器上 7 个进程吞吐最高，更多进程互相争用反而变慢。提取超时或进程退出时终止该进程，下次按需重新启动。
- jsdom 的 `HTMLCollection` 迭代按标准数组迭代器语义直接读取内部列表。原生实现每一步读取 `length` 都会遍历整个集合，使 `Array.from(document.getElementsByTagName('*'))` 成为平方复杂度；在 168 个真实页面上改动前后的提取结果逐字相同，提取耗时减少 27%。
- PDF 转换在常驻转换进程（核数的四分之一，至少 2 个，首次用到时启动）中执行。`pymupdf4llm` 转换期间持有 Python 解释器锁，放在执行线程里会拖慢所有并发项。下载与转换分别受单项时限限制；转换超时时终止该进程，该项记为 `failed`（`timeout`），下次按需重新启动。
- 检索索引由单个索引线程写入：任务项结束后登记资料，索引线程把上一批写入期间积累的资料合成一次 bulk 请求。执行线程不等待索引，也不在索引期间占用数据库连接。任务在全部索引写完后才结束。
- `elasticsearch` 导入需要 1 秒以上。执行器在后台线程中导入它和已注册的预处理模块，并同时启动提取进程，与第一批网络请求并行；`search` 在搜索进行期间同样在后台导入，归档后写索引时不再等待。

默认并发 32 项、同一主机最多 2 项、单项时限 30 秒，可用 `--fetch-concurrency`、`--fetch-per-host`、`--fetch-timeout` 调整。每完成一项立即提交正文，其他项仍在执行时即可读取。单项内部异常记为该项 `failed`（`internal_error`），其他项继续；数据库或文件写入异常使执行器退出，任务显示为 `interrupted`。执行日志每项记录各阶段耗时（`timing`：`prepare`、`request`、`decode`、`parse`、`extract_wait`、`extract`、`classify`、`store`，单位毫秒），每批索引记录资料数与耗时（`index batch=`）。

`task resume` 只把中断时处于执行中的项放回队列，已完成项不再请求；`task retry --failed` 只重新处理失败项；`task cancel` 停止派发，未开始的项记为 `cancelled`，已完成结果保留。没有定时轮询或自动重试。

## 检索索引

字段使用 Elasticsearch 内置 `cjk` 分析器：中文二元切分，英文和数字按标准分词并转小写，无需安装插件。`title`、`summaries`、`body` 另有 `units` 子字段，把“数字+单位”（`%`、`g/m²`、`D`、`dtex`、`支`、`克`、`℃` 等）作为整体词；查询含单位时要求原样命中。索引写入失败时资料记为 `index_state=failed`，归档与读取不受影响，用 `library reindex` 修复。

## 预处理模块接入

`preprocessors/__init__.py` 的 `PREPROCESSORS` 以内容类型（`video`、`podcast`、`pdf`）为键登记模块路径，执行器首次用到时加载。模块提供：

```python
def process(document: dict, hits: list[dict], staging_dir: pathlib.Path, timeout: int) -> dict:
    return {"status": "succeeded", "body": "...", "extractor": "tool 1.0", "metadata": {}}
```

`document` 是 `documents` 表整行，`hits` 是该资料的全部搜索命中（含渠道原始字段 `raw`）。`status` 为 `succeeded`、`partial`、`restricted`、`failed` 或 `not_modified`；`extractor` 必填；可选返回 `technical_reason`、`error`、`http_status`、`final_url`、`response_type`、`restrictions`、`evidence`、`etag`、`last_modified`。结果按上文规则比较与覆盖，资料的 `preprocess_state` 成功时为 `done`，否则为 `failed`。网址或渠道判定为该类型时直接调用模块；网页请求的响应类型为该类型时，执行器保留类型依据并转交模块。

已注册模块：

| 类型 | 模块 | 行为 |
|------|------|------|
| `pdf` | `preprocessors/pdf.py` | 下载 PDF（上限 100 MB），按文件签名 `%PDF-` 确认类型，用 `pymupdf4llm` 的文字层转换为 Markdown（不运行版面模型，不做 OCR）。响应不是 PDF 时交给限制分类：人机验证、登录等页面记为 `restricted`，其他记为 `failed`（`not_pdf`）。没有文字层记为 `failed`（`no_text_layer`），需要密码记为 `failed`（`encrypted`）。元数据含标题、作者、创建时间和页数。 |

视频与播客尚未注册模块，记为 `pending_preprocess`，不发起网络请求，搜索命中的原始元数据保留在 `search_hits.raw`。
