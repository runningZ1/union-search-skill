# Brave 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 网页固定条数未公布 | `page=1`、`max_results=None`，保留当前页全部有效条目；注册表 `default_limit=None` | 可指定第 1–10 页，一次只取指定页，不汇总多页 | 正数仅本地截取，`0` 不截取；不会增大上游单页容量 |

真实结果见 [搜索结果样例](examples/search-result.json)。文件保存统一 CLI 的 `data.results.brave` 渠道对象，包含本地状态与适配后的 `items`，属于 CLI 渠道对象证据层；未保存原始 HTTP 响应或 HTML。容量依据下文已有官方资料与实现说明，样例中的 3 条用于核对字段，不能作为容量上限。

## 常用参数与单次容量

资料核对日期：2026-10-25。参数默认值按 `brave_search.py`、`brave_no_api.py` 和联合入口源码确定。

| 参数 | 默认值 | 含义与实现范围 |
| --- | --- | --- |
| `query` | 必填 | 搜索词，编码为网页参数 `q` |
| `page` / `--page` | `1` | 指定页码，仅允许 1–10，映射为 `offset=page-1`；一次只取指定页 |
| `max_results` / `--max-results` | `None` | 解析后本地截取；`0` 也保留整页，不向网页发送条数参数 |
| `country` / `--country` | `us` | 两字母国家代码或 `all`，通过 Cookie 发送 |
| `safesearch` / `--safesearch` | `moderate` | `off/moderate/strict`，通过 Cookie 发送 |
| `timelimit` / `--timelimit` | `None` | `d/w/m/y` 表示近一天、一周、一个月、一年，映射为 `tf=pd/pw/pm/py` |
| `timeout` / `--timeout` | `20` 秒 | 渠道请求超时；统一 CLI 的 `--timeout` 默认 60 秒 |
| `proxy` / `--proxy` | 未显式指定 | 依次使用传入值、`BRAVE_PROXY`、`NO_API_KEY_PROXY` |
| 统一 CLI `--limit` | `None` | 每渠道结果上限；`0` 不截取，不触发自动翻页 |

单次容量：默认返回第一页中全部可识别的 `data-type="web"` 条目，实际条数随页面变化。正数限制为 `L` 时返回至多 `min(L, 当前页解析条数)`。实现执行一次搜索页 GET，没有跨页汇总；源码确定的页码上限为 10，不能据此推算固定的最大条数。注册表 `default_limit=None`，未定义 `max_limit`，结果数量也没有写死的数值上限。

官方网页单页固定条数与最大条数：未公布；本实现按一次实际页面决定。官方网页帮助说明了翻页和地区、时间筛选，未提供固定容量承诺。本篇容量依据限于公开网页说明。

官方来源（2026-10-25）：[Brave Search 帮助](https://search.brave.com/help)、[网页设置](https://search.brave.com/settings)。本次帮助正文抓取返回 HTTP 429，相关说明由官方页面的联网检索内容核对；未获得固定条数的官方证据。

来源为 `https://search.brave.com/search` 的网页 HTML，`brave_search.py` 只解析 `data-type="web"` 容器；`brave_no_api.py` 继承相同实现。联合搜索名称 `brave_direct` 归并到 `brave`，两者共用本文。网页标题来自 `div.title`，链接来自其最近的祖先 `a`，摘要来自 `generic-snippet` 内的 `div.content`。

函数 `search()` 返回对象数组。脚本使用 `--json` 时顶层为对象，包含 `query:string`、`page:integer`、`country:string`、`total_results:integer`、`results:array<object>`；数量为本次截取后的条目数量，未提供全站命中总数。

| 条目字段 | 类型与缺省 | 来源及含义 |
| --- | --- | --- |
| `title` | 非空 string | 标题节点文本，合并空白，缺失标题直接失败 |
| `url`、`href` | 相同的非空 string | 标题链接的原始 `href`；必须为绝对 HTTP(S) 地址，无跳转解析步骤 |
| `content`、`body` | 相同的 string，可为 `""` | 搜索页摘要区域文本，可能夹带日期、栏目名称 |
| `engine` | string，固定 `brave` | 脚本补充的渠道标识 |

`web_search.result()` 生成上述六个字段，不生成原生排名、发布时间或缩略图。摘要里的日期保持原样，不能直接作为结构化发布时间；没有请求目标网页正文。搜索页其他卡片、广告、图标及丰富结果元数据不在当前提取范围。

联合适配器读取顶层 `results` 并执行 `normalize_item()`：保留 `title/url/content`，删除兼容副本 `href/body`，补充 `published:null`、`thumbnail:null`、`sources:[{platform:"brave",engine:"brave",rank:integer}]`。`rank` 从本渠道返回顺序的 1 开始。URL 删除 fragment、已知跟踪参数并规范主机大小写；仅由这些结构化网页渠道组成的聚合结果通过 `merge_items()` 增加 `id`，按需合并同 URL 来源。

证据为当前两个脚本、`no_api/web_search.py`、`union_search/union_search.py` 与 `structured_results.py`，以及 `.work/output-analysis/no-api.json` 中查询 `sustainable apparel textile industry` 的真实结果：`brave` 成功返回 3 条。首条为 Keypoint Intelligence 的 Sustainability in Textiles and Apparel，摘要包含 `July 23, 2024`，结构化 `published` 仍为 null。实测证实的是适配后字段和摘要语义，原始 HTML 未单独留存。
