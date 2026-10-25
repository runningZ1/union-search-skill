# Wikipedia 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| MediaWiki list=search 的 srlimit 为 1–500、默认 10，也接受 max | 本地 `max_results=None` 时主动发送 srlimit=10；CLI 只接受整数 | 只请求一页，不处理 continue/sroffset | 统一正数传给远端 srlimit 并再次本地截取，本地不夹取到官方范围；统一 `0` 仍请求默认 10 |

真实百科结果见 [搜索结果样例](examples/search-result.json)。文件保存统一 CLI 的 `data.results.wikipedia` 渠道对象，属于 CLI 渠道对象证据层；条目为模块从 query.search 构造的 title/href/body，未保存原始 HTTP JSON、分页信息或命中统计。容量依据下文已有资料，3 条样例验证字段和值。

## 常用参数与返回数量

资料整理日期：2026-10-25。依据 `wikipedia_search.py` 与 MediaWiki 官方 Search 文档；此次未重新执行搜索。

| 参数 | 含义 | 默认值或未指定行为 | 范围与实际约束 |
| --- | --- | --- | --- |
| `query` | 搜索表达式 | 必填 | 发送为 `srsearch`；接口为 `action=query&list=search` |
| `-m/--max-results` | 单次请求数量 | CLI 为 `None`，实现主动发送 `srlimit=10` | 官方 srlimit 为 `1..500`，也接受 `max`；本地 CLI 只接受整数且不夹取、不验证范围，不能传入字符串 max |
| 统一 `--limit` | 每渠道输出上限 | 未指定或 `0` 为 `None`，仍请求 10 | 正整数传为 `-m N`，返回后再次本地切片；超过官方范围没有本地适配保证 |
| `-l/--lang` | Wikipedia 语言站点 | 独立模块为 `en` | 如 `en/zh/ja`，拼接为对应子域名；统一编排遇到中文字符选择 zh，否则使用 en |
| `--proxy` | 网络代理 | 未指定时读取已有 `WIKIPEDIA_PROXY` | 代理 URL；本地不限定枚举 |
| `--json` / `--pretty` | JSON 输出及缩进 | 均为 `false` | pretty 仅影响 JSON 格式，不改变结果数量 |
| 请求 `srprop` / timeout | 命中片段与超时 | 固定 `snippet`、15 秒 | 没有对应独立 CLI 参数；不获取条目全文 |

**官方 Search 模块的 srlimit 默认 10，每请求最多 500 条。** 当前官方说明为 1..500，没有给出本接口需要另行套用的高权限上限。本模块默认明确请求 10 条；虽然独立 CLI 帮助将未指定描述为不限，实际请求仍为 10。

模块只发起一页请求，不处理返回的 `continue/sroffset`，也不自动请求全文。统一 limit 同时影响远端 srlimit 与本地切片；省略它只取消统一层切片，无法取消模块单页数量参数。有效结果可少于请求值，受查询命中、语言站点索引、服务负载与请求限制影响，返回数量不能作为完整命中总数。此处上限适用于实际使用的 list=search，不能引用 OpenSearch 接口上限。

官方来源（资料整理日期：2026-10-25）：[MediaWiki API:Search：srlimit、snippet 与 continuation](https://www.mediawiki.org/wiki/API:Search)。

## 来源与结构

覆盖统一渠道 `wikipedia` 及 `wikipedia_search.py`。通过指定语言站点的 MediaWiki API 查询 `action=query&list=search&srprop=snippet`，读取原生 `query.search[]`。独立 JSON 输出包含 `query`（string）、`lang`（string）、`total_results`（integer，本次返回数）、`results`（array）。统一 CLI 只提取 `results`，存入 `data.items` 或联合结果的 `data.results.wikipedia.items`。

原生 API 中的分页信息与搜索统计不被模块返回。`total_results` 是模块数组长度，不能理解为整个百科中匹配条目的总数。

## 保留字段

| 字段 | 类型 | 原生来源与缺失行为 |
|---|---|---|
| `title` | string | `query.search[].title`，缺失为 `""`；百科条目名 |
| `href` | string | 用 `pageid` 拼接 `https://<lang>.wikipedia.org/?curid=<pageid>`；pageid 为假值时返回空字符串 |
| `body` | string | 来自 `snippet`；移除 HTML 标签并解码实体后去除首尾空白，缺失为 `""` |

`href` 使用页面编号定位文章，没有输出单独的 `pageid` 字段。`body` 是命中片段，不能视为百科完整正文；命中高亮标签已删除，无法再以标签恢复关键词位置。模块不保留 `ns` 等原生字段，也没有单独的相关度评分、作者、发布日期、缩略图、品牌或商品信息。

## 统一 CLI 中的位置

独立入口支持语言参数，默认英文；统一编排遇到关键词含中文字符时选择中文站点，否则使用英文站点，得到条目对象后保持三个字段。联合条目增加的 `_source_platform` 是项目来源标记。`timestamp`、`timing_ms`、`total` 属于搜索状态，不是百科内容属性。日期筛选不能使用请求时间替代文章发布时间。

## 验证范围

以 `sustainable apparel textile industry` 查询成功返回 3 条，确认 `title`、`href`、`body` 均为字符串。证据为 `.work/output-analysis/no-api.json` 的 `data.results.wikipedia.items`；未采集页面正文或其他语言响应。字段映射依据 `wikipedia_search.py` 的 `WikipediaSearch.search()` 与编排器 `_search_wikipedia()`。
