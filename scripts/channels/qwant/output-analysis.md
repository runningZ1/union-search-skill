# Qwant 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 网页固定每页容量与最大条数未公布，未取得官方数值证据 | `max_results=None`，保留默认页全部有效匹配；注册表 `default_limit=None` | 单次 GET，不支持分页或动态加载 | 正数仅本地截取；统一 `--limit 0` 不截取，独立 `--max-results 0` 返回空数组 |

尚无有效结果留样。已有查询及 `.work/output-analysis/sample-recheck.json` 中查询 `服装` 的 `qwant_direct` 均为空结果。证据层为 CLI 渠道对象，`success=true`、`items=[]` 仅说明调用完成，非空业务字段依据源码；未保存原始 HTTP 响应。容量依据下文已有资料，公共字段边界见 [公共输出结构](../no_api/output-analysis.md)。

## 常用参数与单次容量

资料核对日期：2026-10-25。默认值按 `qwant_no_api.py`、共享基类和联合入口核对。

| 参数 | 默认值 | 含义与实现范围 |
| --- | --- | --- |
| `query` | 必填 | 编码为网页查询参数 `q` |
| `max_results` / `--max-results` | `None` | 全页解析后本地切片；独立脚本传 `0` 返回空数组 |
| `timeout` | `15` 秒 | 基类函数请求超时，独立 CLI 未提供此选项；统一 CLI 默认 60 秒 |
| `proxy` / `--proxy` | 未显式指定 | 优先传入代理，其次 `NO_API_KEY_PROXY` |
| `page`、地区、Safe Search | 未提供 | URL 只传查询词，额外关键字不改变 URL；不实现翻页或网页偏好设置 |
| 统一 CLI `--limit` | `None` | 每渠道本地上限；统一入口 `0` 表示不截取 |

单次容量：一次 GET 获取默认网页，保留所有通过标题和链接检查的匹配容器；正数限制 L 后至多输出 `min(L, 当页解析条数)`。没有请求匿名 JSON 搜索接口、加载更多或跨页汇总。注册表 `default_limit=None`，没有 `max_limit` 或固定结果条数上限。

官方默认单页容量与最大条数：未公布，未检索到可核实的官方固定条数承诺；本实现按一次实际页面决定。官方提供地区等设置说明，其存在不表示当前脚本支持对应参数。

官方来源与核实范围（2026-10-25）：[Qwant 搜索帮助](https://help.qwant.com/en/docs/qwant-search/searching/how-to-search-with-qwant/)、[地区设置帮助](https://help.qwant.com/hc/en-us/articles/49002753227153-Set-My-Region-for-Local-Results)。已检索官方内容，搜索帮助正文抓取返回 HTTP 403，未能完整读取该页，容量未作数值推断。

`qwant_no_api.py` 请求 `https://www.qwant.com/?q=...` 的网页 HTML，通过共享 `base_engine.py` 交给 lxml 解析。它没有请求 Qwant 的匿名 JSON 搜索接口，也不运行页面 JavaScript。容器为 class 包含 result 的 `div` 或 class 包含 result-web 的 `article`。

函数返回数组，独立命令 `--json` 顶层为 `{results:array<object>}`。本次返回数量由 `max_results` 切片限制；没有输出上游命中总数、分页令牌、查询回显或其他响应元数据。

| 字段 | 类型、空值及条件 | HTML 来源 |
| --- | --- | --- |
| `title` | 非空 string | `h3` 文本或 class 包含 title 的 `a` 文本并集 |
| `href` | 非空 string | `h3 a` 或标题链接的 `href` |
| `body` | string，缺省 `""` | `p.description` 或 `div.result-desc` 的文本 |
| `engine` | string，固定 `qwant` | 脚本补充 |

标题、链接的匹配列表存在且连接后的内容非空才保留条目。所有文本直接连接后 strip，内部空白没有统一处理，多个链接匹配也会直接连接；单个容器异常会被跳过。正常字段不输出 null，摘要缺失仍保留空字符串。

`href` 保留原页面属性，未补全相对地址、解码跳转或验证 HTTP(S)，其最终目标性质需要实际链接确认。`body` 仅为搜索页描述，没有目标正文。时间文本若落在摘要中，会保留为普通文本，不会生成 `published`。网站图标、缩略图、富卡片、评分、作者及原生排名不在脚本的输出字段中。宽泛的 result 类名匹配也不能作为“所有条目均为普通网页”的格式保证。

联合平台名称 `qwant_direct` 通过通用脚本适配器读取顶层 `results`，渠道 `items` 保留四个字段。当前不经过 `NATIVE_WEB_SCRIPTS` 的 `normalize_item()`，所以没有统一补充 `url/content/published/thumbnail/sources`；聚合的执行时间并非文章时间。

证据为当前 Qwant 脚本、`base_engine.py`、`web_search.py` 与联合适配代码。真实查询 `sustainable apparel textile industry` 在 `.work/output-analysis/no-api.json` 中为 `success:true`、`items:[]`、`total:0`。本次没有成功条目可核对字段实际值；空结果只证明命令完成，无法区分无匹配与动态内容未被静态解析，非空格式由源码确认。
