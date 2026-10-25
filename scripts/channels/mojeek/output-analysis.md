# Mojeek 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 帮助列出每页 10、20、30、40 条，40 为最大设置选项；绝对上限未公布 | 网页默认设置为每页 10 条；模块 `max_results=None` 保留实际解析条目，未发送条数设置 | 单次 GET，不支持分页或修改网页每页设置 | 正数仅本地截取，不能启用每页 40 条；统一 `0` 不截取，独立 `0` 返回空数组 |

尚无有效结果留样。已有真实查询返回 HTTP 403，仅有 CLI 渠道对象的失败状态证据，非空字段及 HTML 映射依据源码；未保存成功条目或原始 HTTP 响应。官方容量依据下文已有帮助资料，公共字段边界见 [公共输出结构](../no_api/output-analysis.md)。

## 常用参数与单次容量

资料核对日期：2026-10-25。实现参数来自 `mojeek_no_api.py`，网页容量说明来自官方搜索帮助。

| 参数 | 默认值 | 含义与实现范围 |
| --- | --- | --- |
| `query` | 必填 | 编码为搜索 URL 的 `q` |
| `max_results` / `--max-results` | `None` | 全页解析后本地切片；独立脚本传 `0` 输出空数组 |
| `timeout` | `15` 秒 | 函数请求超时，独立 CLI 无此选项；统一 CLI 默认 60 秒 |
| `proxy` / `--proxy` | `None` | 传入代理才显式配置；本类不读取渠道代理环境变量 |
| `page`、每页条数、地区 | 未提供 | `search()` 只按查询词构造 URL，额外关键字不用于翻页或容量设置 |
| 统一 CLI `--limit` | `None` | 每渠道本地上限；统一入口 `0` 表示不截取 |

官方网页帮助明确说明默认每页 10 条，可选 20、30、40 条；40 是该帮助列出的最大每页设置选项。官方未承诺每次查询都返回足量条目，也未公布此网页所有情形下的绝对最大返回条数。

单次容量：当前代码只发起一次默认页面 GET，没有发送每页条数参数或保存用户偏好，也不实现分页。默认按官方说明使用每页 10 条设置，实际输出仍取决于当次 HTML 中有效的 `ul.results-standard li`；不能通过 `max_results=40` 启用官方 40 条设置。正数限制 L 仅使输出至多为 `min(L, 当页解析条数)`。注册表 `default_limit=None`，未定义 `max_limit`，源码没有把结果条数限制为 10 或 40。

官方来源（2026-10-25）：[Mojeek 网页搜索技巧](https://www.mojeek.com/support/search/tips.html)，已读取正文；[网页偏好设置](https://www2.mojeek.com/preferences)，官方页面检索说明偏好通过 Cookie 或生成的 URL 保存。容量结论采用网页帮助中的设置范围。

`mojeek_no_api.py` 使用 requests 请求 `https://www.mojeek.com/search?q=...`，通过 lxml 解析网页 HTML。该类独立实现请求和解析，没有继承 `base_engine.py`，也没有使用 `web_search.result()`。解析范围为 `ul.results-standard` 下的 `li`。

函数返回 `list[dict]`；脚本 `--json` 输出 `{results:array<object>}`。解析后按照 `max_results` 切片，没有原生分页信息、查询回显或总命中数。字段表描述脚本产物，网站的 HTML 本身没有这些 JSON 键。

| 字段 | 类型与缺省 | HTML 映射及含义 |
| --- | --- | --- |
| `title` | 非空 string | `h2 a.title` 文本节点，支持 class 完全匹配及包含匹配，连接后 strip |
| `href` | 非空 string | 相同标题链接的 `href`，多个匹配属性直接连接 |
| `body` | string，缺少摘要时 `""` | class 包含 s 的 `p` 文本，以及 `p.s`，使用 XPath 并集 |
| `engine` | string，固定 `mojeek` | 本地补充 |

有标题节点和链接节点且二者内容非空才写入数组；单项解析异常会被跳过。`body` 可缺省为空字符串，正常输出没有 null 值。摘要选择器中的 `contains(@class,'s')` 范围较宽，所以内容范围由实际页面类名决定，不能假设只包含一个纯摘要段落。文本仅连接和去除首尾空白，不提供统一的内部空白归整。

链接为原始网页属性，未补全相对地址、验证协议或解开跳转。摘要是搜索页展示文本，脚本不请求目标正文。网站展示的日期若被摘要选择器覆盖，只会成为 `body` 内文本；不存在单独的发布时间或抓取时间字段。站点图标、排名、缩略图、目录链接等未结构化保留。

联合平台 `mojeek` 通过专用适配读取此脚本，渠道条目继续使用 `title/href/body/engine`。它不属于 `NATIVE_WEB_SCRIPTS`，因此 `normalize_item()` 的 `url/content/published/thumbnail/sources` 契约不适用于该渠道原生 `items`；混合联合集合仍需按实际字段读取。

证据为 Mojeek 脚本及联合适配和标准化范围，并对照共享基类与 `web_search.py` 的差异。`.work/output-analysis/no-api.json` 中真实服装关键词查询返回 HTTP 403，`success:false`、`items:[]`。没有非空成功样本，正常字段与 HTML 映射仅经源码确认，不能据此宣称当前网站结果页已验证可解析。
