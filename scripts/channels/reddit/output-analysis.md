# Reddit 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| Search Listing 默认 25、每请求最多 100，依据下文已有官方索引资料；未验证匿名端点可用性 | 独立搜索 CLI `limit=None` 不发送数量参数；直接调用 YARS 搜索方法默认 10 | 搜索 CLI 只请求一页、不保留游标；YARS 方法提供 after/before；用户活动与帖子列表另有自动分页 | 统一正数既传远端 Listing limit 又本地截取；统一 `0` 不截取且不传远端数量，超过 100 不触发搜索翻页 |

尚无有效结果留样。已有真实搜索仅有 CLI 渠道对象的 `status="failed"`、`items=[]` 与访问失败信息，业务字段依据下文源码分析；未保存成功帖子、评论或原始 HTTP 响应。容量依据已有资料，失败结构不能用于验证成功条目格式。字段边界另见 [公共输出结构](../no_api/output-analysis.md)。

## 常用参数与返回数量

资料整理日期：2026-10-25。参数以 `cli.py`、`yars.py` 为准；此次未重新执行搜索。官方文档页面直接抓取受限，下面的 Listing 数量来自官方 API 文档搜索索引，未通过实际请求再次验证。

| 参数 | 含义 | 默认值或未指定行为 | 范围与实际约束 |
| --- | --- | --- | --- |
| `search query` / `subreddit-search subreddit query` | 全站或子版块帖子关键词搜索 | 查询与子版块名按命令必填 | 全站固定 `sort=relevance&type=link`；子版块另设 `restrict_sr=on` |
| 搜索 `--limit` | 传入 Listing `limit` | CLI 为 `None`，requests 不发送该查询项，采用服务默认 `25`；直接调用 YARS 搜索方法默认 `10` | 官方最大 `100`；本地未校验正数或夹取到 100，超范围行为不能由本地保证 |
| 统一 `--limit` | 每渠道输出上限 | 未指定或 `0` 解析为 `None`，独立搜索不传远端 limit | 正整数既传远端 `limit`，又在返回后切片；超过 100 不会触发搜索翻页 |
| 方法 `after/before` | 选择 Listing 的前后位置 | 均为 `None` | 仅 YARS 方法暴露；搜索 CLI 不提供，也不把返回游标保留下来 |
| 方法 `sort` | 子版块搜索排序 | `relevance` | `search/subreddit-search` CLI 都没有 `--sort`；方法可传服务支持的 `relevance/hot/top/new/comments` |
| `user --limit` / `subreddit-posts --limit` | 用户活动或帖子列表累计数量 | `10` | 两者自动跟随 after；subreddit-posts 每请求 `min(100, limit)`，最终按累计目标停止 |
| `subreddit-posts --category` / `--time-filter` | 列表分类和时间条件 | `hot`、`all` | CLI 分类 `hot/top/new/rising`，但 YARS 不接受 `rising`；时间 CLI 为 `all/day/week/month/year`，主要用于 top |
| `--proxy` / `--timeout` | 网络代理、单请求超时 | 无显式代理、`10` 秒 | timeout 是整数秒，非结果数量保证 |
| `--format` / `--output` | 输出格式及文件 | `display`、stdout | `json/csv/display`；CSV 需要输出文件 |

**官方搜索 Listing 每请求默认 25 条，最多 100 条。** 这是所请求页面的数量参数，不代表全站搜索可遍历的总量承诺。当前 `search/subreddit-search` 只发起一页请求，不自动获取 after 页；统一渠道只使用全站 search。即使不指定统一 limit，也只读取这一页，不会无限获取结果。

用户活动与子版块帖子列表具有独立多页实现；单帖详情只处理响应已给出的评论节点，不扩展 `more`，不能据此承诺取得全部评论。当前调用公开 `.json` 端点，官方文档的 Listing 参数不能保证匿名访问可用；权限、内容删除、索引覆盖、访问策略、频率控制及页面变化都可能使结果减少或请求失败。

官方来源（资料整理日期：2026-10-25）：[Reddit GET search 与 Listing 参数](https://www.reddit.com/dev/api/#GET_search)。本次直接读取受限，最大 100、默认 25 依据该官方页面的搜索索引摘要。

## 依据与验证范围

依据 `cli.py`、`yars.py`、`utils.py`、`reddit_scraper_fallback.py`、`scripts/union_search/union_search.py`、`scripts/cli/adapters.py`、`scripts/cli/output.py` 的当前实现。本文只描述输出格式、字段类型、可空性、来源映射与 CLI 保留范围。

真实样本为根目录 `.work/output-analysis/no-api.json`，查询为 `sustainable apparel textile industry`。其中 `data.results.reddit.success=false`、`status="failed"`、`items=[]`、`total=0`，`error="[]"`，`error_details={code:"ACCESS_DENIED",message:"[]",retryable:false}`。该样本没有成功帖子或评论，以下业务字段来自实现阅读，未经本次真实结果验证。样本顶层 `ok=false` 也包含其他渠道失败，Reddit 的结论以其独立渠道对象为准。

## 搜索层次与返回容器

| 入口 | 业务层次 | JSON 返回类型 |
| --- | --- | --- |
| `cli.py search` → `YARS.search_reddit` | 全站帖子搜索 | `array<object>` |
| `cli.py subreddit-search` → `YARS.search_subreddit` | 指定子版块内的帖子搜索 | `array<object>`，字段与全站搜索一致 |
| `cli.py post` → `YARS.scrape_post_details` | 单个帖子的正文与递归评论 | 成功为 `object`；底层失败返回 `None`，CLI 随后返回非零退出码，不输出成功详情对象 |
| `cli.py user` → `YARS.scrape_user_data` | 用户活动中的帖子、评论 | `array<object>`，用 `type` 区分两种条目 |
| `cli.py subreddit-posts` → `YARS.fetch_subreddit_posts` | 子版块帖子列表 | `array<object>` |

`search` 与 `subreddit-search` 返回帖子摘要，不返回评论树。评论通过 `post` 详情的 `comments` 或 `user` 活动的评论条目取得；当前 CLI 没有独立的全站评论关键词搜索命令。

## 帖子搜索条目

`YARS._handle_search` 从原生 Reddit Listing 的 `data.children[].data` 构造三个字段，原始 Listing 容器与游标不进入输出。

| 输出字段 | 类型及缺失行为 | 来源 |
| --- | --- | --- |
| `title` | 预期 `string`；直接索引，缺失时报错；没有空值归一化 | `title` |
| `link` | `string`，绝对 Reddit 帖子链接 | `"https://www.reddit.com" + permalink` |
| `description` | `string`，缺失时 `""`；显式 `null` 无法进行切片，会报错 | `selftext` 的前 269 个字符 |

条目没有 `id`、作者、分数、评论数、发布时间、子版块、原始外部链接、完整正文。`link` 指向讨论页面。`description` 可以为空，链接类帖子常无 `selftext`；它没有省略标志，也不是评论摘要。

## 单帖详情与递归评论

详情读取 Reddit 返回的两个 Listing：第一个提供主帖，第二个提供评论。

| 字段路径 | 类型与可空性 | 来源映射 |
| --- | --- | --- |
| `title` | 预期 `string`；直接索引 | 主帖 `title` |
| `body` | 预期 `string`；缺失默认 `""`，显式 `null` 保留 | 主帖 `selftext`，完整保留 |
| `comments` | `array<object>`，可以为空 | 第二个 Listing 的评论节点 |
| `comments[].author` | 预期 `string`；缺失默认 `""`，显式 `null` 保留 | 评论 `data.author` |
| `comments[].body` | 预期 `string`；缺失默认 `""`，显式 `null` 保留 | 评论 `data.body` |
| `comments[].score` | 正常为 `integer`；缺失默认 `""`，因此实现允许整数与字符串两种形态；显式 `null` 保留 | 评论 `data.score` |
| `comments[].replies` | 始终为 `array<object>`，叶节点为 `[]` | 递归处理评论 `replies.data.children`，子节点字段同上 |

评论树仅包含 `kind="t1"` 的节点，`more` 占位节点没有对应输出，因此 `comments=[]` 不能证明帖子没有评论。输出不包含评论 `id`、`parent_id`、链接、发布时间，也不保留主帖的作者与计数字段。层级关系由嵌套的 `replies` 表达。

## 用户活动与子版块列表

用户活动条目来自原生 `kind="t3"` 和 `kind="t1"`：

| 条目类型 | 输出字段 | 类型与来源 |
| --- | --- | --- |
| 帖子 | `type="post"`、`title`、`subreddit`、`url`、`created_utc` | `title/subreddit` 直接取同名字段；`url` 拼接 Reddit 域名与 `permalink`；`created_utc` 正常为 Unix 秒数 `number` |
| 评论 | `type="comment"`、`subreddit`、`body`、`created_utc`、`url` | `body` 为评论正文；其余来源同上；没有 `title` 或递归回复 |

这些源字段使用 `.get(..., "")`：缺失时返回空字符串，显式 `null` 保留；拼接得到的 `url` 始终是字符串。用户活动中的 `type` 是适配器新增的业务标识，原生 `kind` 不保留。

子版块列表始终构造 `title`、`author`、`permalink`、`score`、`num_comments`、`created_utc`，分别直接读取主帖同名字段。预期类型依次为 `string/string/string/integer/integer/number`，缺失时报错；`permalink` 是相对路径。可选 `image_url:string` 来自帖子 `url` 或 `preview.images[0].source.url`，可选 `thumbnail_url` 来自 `thumbnail`。这些可选字段没有统一空值处理；缩略图字符串也可能是服务端状态文字。列表没有 `body`、`description` 和评论树。

## 独立脚本与输出格式

`cli.py --format json` 将上述业务对象或数组直接序列化，没有统一 CLI 的信封。`display` 输出标题与完整条目的格式化 JSON；`csv` 使用第一条记录的键作为列名，嵌套回复不会展开成关系表，单帖详情对象也不符合该导出函数要求的记录数组结构。

同目录 `reddit_scraper_fallback.py` 是另一套独立输出：帖子数组包含 `title`、`author`、`score`、`num_comments`、`url`、`subreddit`、`created_utc`、`flair`、`selftext`、`is_self`、`upvote_ratio`。其中 `url` 为 `redd.it` 短链接或 Reddit permalink；`created_utc` 转为 `integer`；`selftext` 通过 `or ""` 归一化；`flair` 从 `link_flair_text` 映射，可能为 `null`；其他 `.get` 字段保留显式 `null`。该脚本不提供评论结构。当前统一 CLI 的 Reddit 路径调用 `cli.py search`，没有接入这套字段。

## 统一 CLI 的保留范围

`scripts/union_search_cli.py search` 的 Reddit 适配器解析 `cli.py search --format json` 返回的数组，保留条目的 `title/link/description`，没有改名为 `url/snippet`。`platform reddit` 使用相同搜索路径，不提供 `post`、`user` 或评论搜索结果。

`data.results.reddit` 包含 `platform:string`、`keyword:string`、`success:boolean`、`error:string|null`、`items:array<object>`、`total:integer`、`timestamp:string`、`timing_ms:integer`、通常存在的 `status:string`。成功执行还会写入 `has_results:boolean`，空结果增加 `warning:string`；失败可增加 `error_details:object`，失败样本没有 `has_results`。`total` 为实际条目数。

联合搜索的 `data.final_items` 复制成功条目并增加 `_source_platform="reddit"`。原有字段保留；失败渠道不贡献条目。CLI 另外增加 `download_candidates`、计时、渠道状态与汇总，不会补全 Reddit 业务字段。

顶层信封包含 `schema_version/ok/type/success/command/query/timestamp/duration_ms/errors/meta/data`；失败时增加 `error` 对象。任一渠道失败会使搜索顶层 `ok=false`，仍保留各渠道数据。统一 CLI 的 JSON、text 和搜索 Markdown 输出都保留完整字段；Markdown 将信封放入 JSON 代码块。当前真实样本只验证了 Reddit 失败结构。
