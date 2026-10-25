# DuckDuckGo Instant 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 固定最大条数未公布，官方文档未提供数量参数 | `max_results=None`，保留有效 Abstract、Results 和递归深度小于 2 的 RelatedTopics 叶子；注册表 `default_limit=None` | 不支持分页，每次请求一次 API | 正数仅本地截取；统一 `--limit 0` 不截取，独立 `--max-results 0` 返回空数组 |

真实查询 `textile` 见 [搜索结果样例](examples/search-result.json)，包含 3 条 `related` 结果。文件保存统一 CLI 的 `data.results.duckduckgo_instant` 渠道对象，属于 CLI 渠道对象证据层；`items` 为脚本解析结果，未保存原始 HTTP JSON。Abstract 与 Results 的非空字段仍依据源码说明，样例条数不代表接口容量上限。

## 常用参数与单次容量

资料核对日期：2026-10-25。该渠道使用 Instant Answer API，容量按一次 JSON 响应分析。

| 参数 | 默认值 | 含义与实现范围 |
| --- | --- | --- |
| `query` | 必填 | 编码为 API 参数 `q` |
| `max_results` / `--max-results` | `None` | 全部解析后本地切片；独立脚本传 `0` 会得到空数组 |
| `timeout` | `15` 秒 | 函数的请求超时，独立 CLI 没有此选项；统一 CLI 超时默认 60 秒 |
| `proxy` / `--proxy` | `None` | 传入代理才显式配置 Session 代理，无渠道环境变量读取逻辑 |
| `format` | 固定 `json` | 请求 JSON，当前脚本不提供修改入口 |
| `no_redirect` | 固定 `1` | 按官方说明跳过 `!bang` 的 HTTP 跳转 |
| `no_html` | 固定 `1` | 按官方说明移除文本中的 HTML 格式 |
| `page` | 未提供 | 不支持页码和自动分页 |
| 统一 CLI `--limit` | `None` | 每渠道本地上限；统一入口将 `0` 解释为不截取，与独立脚本不同 |

单次容量：只请求一次 API。解析容量为至多 1 条有效 Abstract，加上有效 Results 条目数，再加上递归深度小于 2 的有效 RelatedTopics 叶子数；每项要求说明和地址同时非空。默认 `max_results=None` 保留这些解析结果，设置正数 L 后至多返回 `min(L, 解析总数)`。更深层叶子被丢弃，组名称不作为条目。注册表 `default_limit=None`，没有 `max_limit` 或硬编码的总条数上限。

官方最大返回条数：未公布。官方文档未提供分页或条数请求参数，不能通过增加本地 limit 获取更多答案；单次可用数量由 API 实际响应和上述解析条件决定。该接口提供即时答案、定义与相关主题，其容量无需按网页页数解释。

官方来源（2026-10-25）：[DuckDuckGo 官方仓库中的 Instant Answer API 文档](https://github.com/duckduckgo/duckduckgo-publisher/blob/master/share/site/duckduckgo/api.tx)、[同一文档原文](https://raw.githubusercontent.com/duckduckgo/duckduckgo-publisher/master/share/site/duckduckgo/api.tx)。已读取原文并核对 `AbstractText/Results/RelatedTopics` 与请求参数；仓库属于归档资料，文档未承诺当前固定容量。

`duckduckgo_instant.py` 调用 `https://api.duckduckgo.com/` 的匿名 JSON Instant Answer 接口，使用 `format=json&no_redirect=1&no_html=1`。内容范围为即时答案、主要结果与相关主题。函数返回数组，脚本 `--json` 包装为 `{results:array<object>}`；上游响应对象本身不会完整输出。

| 条目字段 | 类型、缺省及条件 | 原生来源 |
| --- | --- | --- |
| `title` | 非空 string | abstract 使用 `AbstractSource`，为空时截取 `AbstractText` 前 50 字符；其他类型取 `Text` 在 ` - ` 前的部分，再截取 80 字符 |
| `href` | 非空 string | abstract 使用 `AbstractURL`，其他类型使用 `FirstURL`；仅检查非空，没有验证绝对地址 |
| `body` | 非空 string | `AbstractText` 或 `Text` 去除首尾空白，保存答案或主题说明 |
| `engine` | string，固定 `duckduckgo_instant` | 脚本补充 |
| `type` | string 枚举 | `abstract`、`result`、`related`，用于区分答案来源 |

输出顺序依次为 Abstract、Results、RelatedTopics。Abstract 需要说明和 URL 同时非空；主要结果需要 `Text/FirstURL` 同时非空。相关主题遇到 `Topics` 组时递归访问，仅保留递归深度小于 2 的叶子；组名称、层级、图标和更深层叶子均不输出。没有答案时允许正常返回空数组。接口其他即时回答属性不经此解析函数转存，不能依靠输出还原完整原生响应。

`body` 是接口提供的答案或简述，没有提取目标网页全文，也不提供独立发布时间、排名、缩略图或可信度。URL 直接来自来源字段，脚本没有跟踪跳转。文字内即使存在日期或年份，也只属于答案文本。

联合搜索通过专用适配调用，渠道 `items` 保留 `title/href/body/engine/type`，此渠道未进入 `NATIVE_WEB_SCRIPTS`，不会自动增加 `url/content/published/thumbnail/sources`。混合联合结果可增加聚合来源标记，但 `type` 仍是本渠道有意义的筛选字段；不能把通用网页标准化契约套用到该原生数组。

证据为当前脚本及联合适配、标准化范围。`.work/output-analysis/no-api.json` 中真实查询 `sustainable apparel textile industry` 执行成功，`items:[]`、`total:0`。另一次真实查询 `textile` 保存于 `.work/output-analysis/duckduckgo-instant-textile.json`，返回 3 条，实际字段均为 `title/href/body/engine/type`，type 均为 related，链接分别指向 DuckDuckGo 的 Textile、Textile_industry 与 Textile_(markup_language) 页面。该样本说明主题消歧结果可混入同名标记语言，title 可能由说明文本截断而来。abstract、result 类型与递归边界仍仅由源码确认；没有保存完整上游 JSON。
