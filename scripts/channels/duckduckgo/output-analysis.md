# DuckDuckGo 网页输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 网页每批固定容量与最大条数未公布 | `page=1`、`max_results=None`，保留首批全部有效条目；注册表 `default_limit=None` | 沿原生下一批地址访问至指定页，只保留该页；无本地页码数值上限 | 正数本地截取指定批次，`0` 不截取；不会按目标数量自动汇总批次 |

真实结果见 [搜索结果样例](examples/search-result.json)。文件为统一 CLI 的 `data.results.duckduckgo` 渠道对象，包含适配后的条目与执行状态，属于 CLI 渠道对象证据层；原始 HTML 和 `/d.js` HTTP 响应未保存。容量依据下文已有资料，3 条样例仅证明实际字段和值。

## 常用参数与单次容量

资料核对日期：2026-10-25。参数默认值来自两个 DuckDuckGo 脚本与联合入口源码。

| 参数 | 默认值 | 含义与实现范围 |
| --- | --- | --- |
| `query` | 必填 | 查询长度 1–499 字符，且不能全为空白 |
| `page` / `--page` | `1` | 正整数；沿原生 `n` 下一页地址访问到指定页，只返回该页结果 |
| `max_results` / `--max-results` | `None` | 当前页解析后本地截取；`0` 也保留整页，不控制上游容量 |
| `region` / 主脚本 `--region` | `wt-wt` | 本实现只允许该值，其他地区直接失败 |
| `timelimit` / 主脚本 `--timelimit` | `None` | 本实现不支持时间筛选，传入任何非空值直接失败 |
| `timeout` / `--timeout` | `20` 秒 | 首页及遍历结果页共用截止时间；统一 CLI 默认 60 秒 |
| `proxy` / `--proxy` | 未显式指定 | 依次取传入值、`DUCKDUCKGO_PROXY`、`NO_API_KEY_PROXY` |
| 统一 CLI `--limit` | `None` | 每渠道结果上限；`0` 不截取，不因数量要求继续翻页 |

单次容量：默认输出第一批 `/d.js` 响应中全部含 `u` 的有效条目。请求指定第 P 页时，先请求首页发现接口，再顺序请求至多 P 批结果；只保留第 P 批，不合并前面的页面，提前没有下一页地址时返回空数组。正数限制 L 的输出至多为 `min(L, 指定批次有效条数)`。注册表 `default_limit=None`，源码未定义 `max_limit` 或页码数值上限，也没有固定每批条数。

官方网页每批固定容量与最大条数：未公布；本实现按一次实际结果响应决定。官方 URL 参数页说明了分页显示和自动加载等网页设置；其中地区参数的可用性不代表本脚本支持地区筛选。没有将即时答案接口的字段或容量用于推断此网页渠道。

官方来源（2026-10-25）：[DuckDuckGo 网页 URL 参数说明](https://duckduckgo.com/duckduckgo-help-pages/settings/params/)，已读取正文，未发现固定最大结果数承诺。

`duckduckgo_search.py` 先读取首页 HTML 的 `deep_preload_link`，再请求匿名 `/d.js?o=json` 接口，读取 JSON 顶层 `results` 数组。当前来源包含 HTML 发现接口与匿名 JSON 结果两个阶段。`duckduckgo_no_api.py` 的兼容类沿用该实现；联合名称 `duckduckgo_html` 归并到 `duckduckgo`，名称中的 html 不表示当前采用静态 HTML 结果列表。

函数返回对象数组。主脚本 JSON 顶层包含 `query:string`、`page:integer`、`total_results:integer`、`results:array<object>`；兼容脚本打印的顶层仅有 `results`。`total_results` 为当前返回条数。原生行中的 `n` 用于下一页接口地址，不输出为搜索条目；没有 `u` 的行被跳过。

| 原生字段或脚本字段 | 类型与缺省 | 处理与语义 |
| --- | --- | --- |
| `t` → `title` | 输出为非空 string | 必需标题，解析 HTML fragment 后提取文本、合并空白 |
| `u` → `url/href` | 相同的非空 string | 目标地址，必须为绝对 HTTP(S)；可直接指向 PDF |
| `a` → `content/body` | 输出 string，缺省 `""` | 搜索摘要，去除 HTML 标记 |
| `engine` | string，固定 `duckduckgo` | 脚本增加 |
| `source_rank` | integer，从 1 开始 | 当前页有效条目位置，过滤掉无 `u` 行后计算 |

JSON 其他原生属性均未整体透传。摘要没有单独的日期解析，缺省摘要不影响标题和链接有效的条目。脚本不下载目标正文，标题中的年份和摘要里的日期都保留为普通文本。

联合适配先读取脚本 `results`，再标准化为 `title/url/content/published/thumbnail/sources`。`source_rank` 不保留；`sources[].rank` 按适配后输入次序重新生成。`published`、`thumbnail` 均为 null，来源的 `platform/engine` 均为 `duckduckgo`。标准化 URL 去除 fragment 与已知跟踪参数；完全由结构化网页渠道组成的最终集合增加 `id` 并支持合并同 URL 来源，混合分组的最终形状应以实际聚合结果为准。

证据为两个 DuckDuckGo 脚本、`web_search.py` 和联合标准化代码。真实查询 `sustainable apparel textile industry` 见 `.work/output-analysis/no-api.json`：渠道成功返回 3 条，包括 ScienceDirect 文章和一个 PDF 地址，均有摘要且 `published:null`。这确认了标准化输出；原始 `/d.js` JSON 未单独保存，原生 `t/u/a/n` 的解释来自源码。
