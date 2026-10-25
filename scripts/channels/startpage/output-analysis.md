# Startpage 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 网页默认每页容量与最大条数未公布，未取得官方数值证据 | `max_results=None`，保留默认页全部有效匹配；注册表 `default_limit=None` | 单次 GET，不支持分页或动态加载 | 正数仅本地截取；统一 `--limit 0` 不截取，独立 `--max-results 0` 返回空数组 |

尚无有效结果留样。已有查询及 `.work/output-analysis/sample-recheck.json` 中查询 `服装` 的 `startpage_direct` 均为空结果。证据层为 CLI 渠道对象，空集合仅能核对执行状态，非空业务字段依据源码；未保存原始 HTTP 响应。容量依据下文已有资料，公共字段边界见 [公共输出结构](../no_api/output-analysis.md)。

## 常用参数与单次容量

资料核对日期：2026-10-25。默认值来自 `startpage_no_api.py`、共享基类与联合入口。

| 参数 | 默认值 | 含义与实现范围 |
| --- | --- | --- |
| `query` | 必填 | 编码为网页参数 `q` |
| `max_results` / `--max-results` | `None` | 全页解析后本地切片；独立脚本传 `0` 返回空数组 |
| `timeout` | `15` 秒 | 基类请求超时，独立 CLI 没有该选项；统一 CLI 默认 60 秒 |
| `proxy` / `--proxy` | 未显式指定 | 依次取传入代理、`NO_API_KEY_PROXY` |
| `page`、语言、地区、每页条数 | 未提供 | URL 只传查询词，额外关键字不改变 URL；没有翻页或偏好设置实现 |
| 统一 CLI `--limit` | `None` | 每渠道本地上限；统一入口 `0` 表示不截取 |

单次容量：一次 GET 读取默认搜索页，默认保留全部标题和链接均有效的匹配容器。正数限制 L 后至多输出 `min(L, 当页解析条数)`，不通过本地 limit 请求更多结果。注册表 `default_limit=None`，没有 `max_limit` 或硬编码的结果条数上限，不自动翻页或加载动态内容。

官方默认每页容量与最大条数：未公布，未核实到固定条数承诺；本实现按一次实际页面决定。

官方来源与核实范围（2026-10-25）：[Startpage 搜索使用说明](https://support.startpage.com/hc/en-us/articles/4521418101524-How-to-use-Startpage-more-effectively)、[官方设置帮助目录](https://support.startpage.com/hc/en-us/sections/4481942717076-Settings)。已联网检索官方内容，使用说明正文抓取未成功，未从第三方设置教程推断当前容量。

`startpage_no_api.py` 请求 `https://www.startpage.com/do/search?q=...` 的网页 HTML，继承 `no_api/base_engine.py`，通过 lxml 静态解析。结果容器选择 class 包含 result 的 `li` 与 class 包含 search-result 的 `div`；代码未使用匿名 JSON 接口，也没有执行浏览器脚本。

函数返回对象数组，命令 `--json` 输出 `{results:array<object>}`。数组在解析后受 `max_results` 限制，顶层没有保留分页、原生命中总数或查询字符串。

| 字段 | 类型、缺省及条件 | HTML 映射 |
| --- | --- | --- |
| `title` | 非空 string | `h3` 文本或 class 包含 title 的链接文本并集 |
| `href` | 非空 string | `h3 a` 或标题链接的 href 属性 |
| `body` | string，缺省 `""` | class 包含 desc 的 `p` 与 class 包含 snippet 的 `div` 文本 |
| `engine` | string，固定 `startpage` | 脚本补充 |

标题、链接都必须有匹配节点且连接后非空。多个节点使用空字符串连接再 strip，不主动添加分隔符或归整内部空白；单条解析错误会被跳过。摘要节点缺失时 `body` 仍存在且为空字符串，正常输出没有 null 类型。

链接字段仅复制页面属性，未执行 `urljoin`、协议验证、服务包装地址解析或后续重定向请求，因此无法仅凭 href 确认是完整的最终地址。脚本没有分别保留匿名浏览入口与目标链接。`body` 是结果页摘录，没有访问目标正文；日期、来源站名若处于摘录选择器内会留在普通文本中，未提取 `published`。图片、网站图标、丰富结果、广告状态和排名均没有独立字段。

联合平台 `startpage_direct` 经通用脚本适配读取顶层 `results`，渠道 `items` 沿用 `title/href/body/engine`。该渠道不进入 `NATIVE_WEB_SCRIPTS` 的标准化阶段，所以不能预期自动获得 `url/content/published/thumbnail/sources`。联合信封与渠道记录中的时间是执行时间，不能作为页面更新时间。

证据为本渠道脚本、共享基类、`web_search.py` 和联合适配范围。真实查询 `sustainable apparel textile industry` 在 `.work/output-analysis/no-api.json` 中为执行成功、`items:[]`、`total:0`。没有非空响应样本，字段定义及 HTML 映射仅由源码确认；空数组无法区分真实无结果、页面结构变化或动态展示内容。
