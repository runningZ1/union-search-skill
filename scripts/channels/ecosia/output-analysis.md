# Ecosia 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 网页默认每页条数与最大条数未公布 | `max_results=None`，保留默认页全部有效条目；注册表 `default_limit=None` | 单次 GET，不支持分页或动态加载 | 正数仅本地截取；统一 `--limit 0` 不截取，独立 `--max-results 0` 返回空数组 |

尚无有效结果留样。已有真实调用为 HTTP 403 失败，仅能证明 CLI 渠道对象中的失败状态，业务字段由下文源码说明确认；未保存成功条目或原始 HTTP 响应。本篇容量依据已有官方资料与实现，失败条数不能作为正常容量证据。公共字段边界见 [公共输出结构](../no_api/output-analysis.md)。

## 常用参数与单次容量

资料核对日期：2026-10-25。默认值由 `ecosia_no_api.py`、`base_engine.py` 与联合入口确定。

| 参数 | 默认值 | 含义与实现范围 |
| --- | --- | --- |
| `query` | 必填 | 编码为搜索 URL 的 `q` |
| `max_results` / `--max-results` | `None` | 本地 `results[:max_results]`；独立脚本传 `0` 返回空数组 |
| `timeout` | `15` 秒 | 基类函数请求超时，独立 CLI 未提供此选项；统一 CLI 默认 60 秒 |
| `proxy` / `--proxy` | 未显式指定 | 传入代理优先，其次 `NO_API_KEY_PROXY` |
| `page`、地区、时间筛选 | 未提供 | URL 只发送查询词；函数额外关键字不改变该 URL，不实现翻页 |
| 统一 CLI `--limit` | `None` | 每渠道本地条数限制；统一入口的 `0` 表示不截取 |

单次容量：一次 GET 读取默认搜索页面，默认保留当页所有通过标题和链接检查的匹配容器。正数限制 L 只把输出截为至多 `min(L, 当页解析条数)`；不会发送上游条数、请求下一页或加载动态结果。注册表 `default_limit=None`，没有 `max_limit` 或固定条数上限。

官方默认每页条数与最大条数：未公布；本实现按一次实际页面决定。官方设置文章介绍地区、语言、提供商与 Safe Search 等设置，没有给出固定结果数量承诺；本脚本没有实现这些设置参数。

官方来源（2026-10-25）：[Ecosia 搜索设置](https://support.ecosia.org/article/349-ecosia-settings)，已读取正文；[搜索提供商说明](https://support.ecosia.org/article/579-search-results-providers)，经官方页面检索核对。

`ecosia_no_api.py` 请求 `https://www.ecosia.org/search?q=...`，输入来源为网页 HTML。它继承 `no_api/base_engine.py`，用 lxml 解析响应；没有调用 Ecosia JSON API，也没有浏览器执行页面脚本。结果容器匹配 `article` 的 result 类名或 `div.result-web`。

函数返回 `list[dict]`；命令携带 `--json` 时输出对象 `{results:array<object>}`。顶层没有查询回显、页面编号或全站总数，数组经过 `max_results` 截取。

| 字段 | 类型、缺省与条件 | HTML 来源 |
| --- | --- | --- |
| `title` | 非空 string | `h3` 文本与 `a.result-title` 文本的 XPath 并集，直接连接后去除首尾空白 |
| `href` | 非空 string | `h3 a` 或 `a.result-title` 的 `href`，多个匹配值直接连接 |
| `body` | string，可为 `""` | `p.result-snippet` 或 `div.result-abstract` 文本连接 |
| `engine` | string，固定 `ecosia` | 脚本补充渠道名 |

标题、链接都存在且去除空白后非空才加入数组，单项解析异常被跳过。字段不会按正常输出写入 null；摘要节点缺失时写入空字符串。只有首尾空白被处理，内部文本间隔没有统一折叠，文本连接也不会主动插入分隔符。

`href` 是页面属性原值，代码没有执行 `urljoin`、解开服务跳转或校验协议，因此只能按来源链接理解，无法由字段名保证是最终落点。`body` 表示搜索页摘要，不包含目标全文。日期、站点名称若在摘要区域出现，会混入 `body`；没有独立时间字段。图片、网站图标、排名、页码、广告标识和命中总量均未保留。

联合名称为 `ecosia_direct`，通用脚本适配器取顶层 `results` 作为渠道 `items`，保留四个原生字段。当前该渠道不在 `NATIVE_WEB_SCRIPTS`，不执行 `normalize_item()`，因此没有保证补充 `published/thumbnail/sources`；筛选时从 `href/body` 读取链接与摘要。联合信封的时间表示执行时间，与网页发布时间无对应关系。

证据为 Ecosia 脚本、`base_engine.py`、`web_search.py` 和联合适配代码。真实服装关键词查询见 `.work/output-analysis/no-api.json`：`ecosia_direct` 因 HTTP 403 失败，条目为空。本篇非空字段及 HTML 映射仅由源码确认，没有成功响应样本；失败状态不应作为正常原生条目格式。
