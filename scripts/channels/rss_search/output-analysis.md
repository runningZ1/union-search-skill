# RSS 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| RSS 无统一搜索条数上限；规范允许任意数量 item，实际历史窗口由发布者决定 | 独立 `limit=10`，多源依配置顺序合并后保留最多 10 条 | 每个 feed URL 读取一次，不跟随分页或归档链接；归档读取只选择最新文件 | 独立正数 limit 在全部源合并后本地截取，`0` 或负数取消截取；未接入统一 CLI，统一 limit 不适用 |

真实 Guardian Fashion 搜索结果见 [搜索结果样例](examples/search-result.json)。文件保存独立 `rss_search.py --json` 返回的结果数组，属于独立响应证据层；未包装统一 CLI 信封，也未保存原始 HTTP RSS/Atom XML。3 条样例可核对 HTML summary、对象数组 tags 与日期文本，容量依据下文已有规范与实现。

## 常用参数与返回数量

资料整理日期：2026-10-25。依据 `rss_search.py`、RSS 2.0 规范与 feedparser 文档；此次未重新获取订阅源或执行搜索。

| 参数 | 含义 | 默认值或未指定行为 | 范围与实际约束 |
| --- | --- | --- | --- |
| `query` | 在标题与 summary 中匹配连续关键词 | 空字符串，保留全部条目 | 字符串包含匹配；不搜索 content 正文，也不做搜索引擎式查询解释 |
| `--feed` / `--feeds` | 单个源或源列表文件 | 均省略时使用代码内 DEFAULT_RSS_FEEDS | feed 优先于 feeds；列表支持 URL 或名称加 URL，每行一个 |
| `-l/--limit` | 全部源合并后的本地数量上限 | `10` | 大于零时执行 `all_results[:N]`；0 和负数都取消此切片，没有固定数字上限 |
| `--case-sensitive` | 区分大小写 | `false` | false 时标题与 summary 转小写后匹配 |
| `--parse-folder` | 保存解析归档，或配合 no-fetch 读取归档 | 空字符串，不使用归档模式 | 路径；读取时只选择最新 all_feeds 文件，没有自动合并历史记录 |
| `--parse-only` / `--no-fetch` | 仅保存解析结果 / 只读已保存结果 | 均为 `false` | 需要 parse-folder 才进入对应分支；parse-only 不执行搜索，no-fetch 不访问订阅源 |
| `--timeout` | 声明的请求超时秒数 | `30` | 虽传入 fetch_rss_feed，但当前没有传给 `feedparser.parse`，不能保证此参数实际控制网络超时 |
| `--json/--pretty/--markdown` | 输出格式与缩进 | 默认文本 | JSON 优先于 Markdown，pretty 只影响 JSON 缩进 |
| `--full` / `--output` | 详情展示与输出文件 | false、stdout | full 不扩充搜索 JSON 字段；结果无 content 键，启用完整文本展示可能在读取该键时失败 |

**RSS 没有统一的“官方搜索每请求最多多少条”。** RSS 2.0 规范允许 channel 包含任意数量 item；每个源实际保留的历史窗口和条目数量由发布者决定，不能把规范允许任意数量解释为源站提供无限历史。模块读取的是订阅文件，再在本地过滤，没有向源发送搜索请求或 limit 参数。

当前实现每个 feed URL 读取一次，不跟随 feed 中的分页、归档或下一页链接；多源依配置顺序合并，随后统一执行本地 limit，不按时间重新排序。默认最终最多输出 10；0 或负数保留当前已加载的全部匹配项，数量仍受每个源本次文件内容限制，没有固定本地数字上限。匹配不足、源站保留策略、发布更新、网络失败、访问控制或解析问题都会减少结果。

RSS 模块未注册为统一 CLI 渠道，统一 `--limit` 不适用于该入口；这里的 --limit 完全属于本地输出截断。归档解析模式可以保存全部已解析条目，搜索输出的 limit 不限制归档文件的 entries 数量。

官方及库来源（资料整理日期：2026-10-25）：[RSS 2.0 规范：item 数量](https://www.rssboard.org/rss-specification)、[feedparser 官方文档](https://feedparser.readthedocs.io/en/latest/)。这些来源没有为各发布者的订阅源承诺统一搜索返回数量。

## 来源与输出层次

独立入口 `rss_search.py` 使用 feedparser 读取真实 RSS/Atom feed，在条目 title 与 summary 中匹配查询。该模块未注册为统一 CLI 渠道。`--json` 正常输出结果数组，没有统一信封或顶层 total；`--full` 不会扩大 JSON 的字段集合，主要作用于文本/Markdown 展示。

## 搜索结果字段

| 字段 | 类型 | 来源与缺失规则 |
|---|---|---|
| `title` | string | feedparser 条目 title，缺失为 `""` |
| `link` | string | 原始条目 link，缺失为 `""` |
| `weixin_link` | string | 条目已有 weixin_link 或从 summary 提取的微信地址；没有时可能直接使用 link，因此字段名不保证地址属于微信 |
| `published` | string | 原始 published 文本，缺失为 `""`；搜索输出不调用日期格式化辅助函数 |
| `author` | string | 条目 author，缺失为 `""` |
| `summary` | string | feedparser 条目 summary，网络搜索路径保留 HTML；不是统一纯文本或完整原文 |
| `tags` | array | 原始条目 tags，缺失为 `[]`；通常元素为含 term、scheme、label 的对象，不能按字符串数组使用 |
| `feed_title` | string | 所属 feed 标题；用于区分来源站点 |
| `feed_url` | string | 本次读取的 feed 地址，区别于文章 link |

模块不会为每条结果补充 score、rank、缩略图或内容全文。发布者提供的 summary 长短不同；其中价格、面料和品牌文字没有进一步结构化。

## 解析归档与搜索输出的区别

`--parse-folder` / `--parse-only` 另行保存 feed 对象数组：每项包括 url、title、description、link、entries、status，可能含 error、parsed_at。entries 保留 feedparser 的扩展字段，例如 id、links、content、published_parsed、updated 等，实际集合由订阅源决定。这个解析归档比最终搜索结果宽，不应把归档字段全部当作搜索字段。

保存归档时会清理 summary、description 和首个 content.value 的 HTML。直接联网搜索的 summary 仍可能含 HTML，读取已保存归档的搜索则可能得到纯文本，两种路径的值形态不同。时间通常保留 RSS 原始格式；标签缺少 scheme/label 时也可能有 null。

## 验证范围

以真实 Guardian Fashion feed `https://www.theguardian.com/fashion/rss` 查询 `fashion`，成功保存 3 条至 `.work/output-analysis/rss.json`，确认 summary 含 HTML、tags 为对象数组，published 为带 GMT 的日期字符串，weixin_link 实际仍为 Guardian 地址。未穷举各 feed 的扩展字段。实现依据 `search_entries()`、`_fetch_and_search_feed()`、`save_parsed_feeds()`。
