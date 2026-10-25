# 集思录输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 搜索页固定容量与最大条数未公布，未取得官方数值证据 | `max_results=None`，保留默认页全部有效匹配；注册表 `default_limit=None` | 单次 GET，不支持分页 | 正数仅本地截取；统一 `--limit 0` 不截取，独立 `--max-results 0` 返回空数组 |

尚无有效结果留样。已有查询及 `.work/output-analysis/sample-recheck.json` 中查询 `服装` 的 `jisilu_direct` 均为 `items=[]`、`status="empty"`。证据层为 CLI 渠道对象，空结果只能核对执行状态，非空业务字段依据源码；未保存原始 HTTP 响应。容量依据下文已有资料，公共字段边界见 [公共输出结构](../no_api/output-analysis.md)。

## 常用参数与单次容量

资料核对日期：2026-10-25。默认值来自 `jisilu_no_api.py`、共享基类和联合入口。

| 参数 | 默认值 | 含义与实现范围 |
| --- | --- | --- |
| `query` | 必填 | 编码为 `https://app.jisilu.cn/search/` 的 `q` |
| `max_results` / `--max-results` | `None` | 解析后本地切片；独立脚本传 `0` 返回空数组 |
| `timeout` | `15` 秒 | 基类函数请求超时，独立 CLI 没有此选项；统一 CLI 默认 60 秒 |
| `proxy` / `--proxy` | 未显式指定 | 依次取传入值、`NO_API_KEY_PROXY` |
| `page`、排序、证券类别 | 未提供 | URL 只传查询词，额外关键字不改变 URL，不提供翻页或分类请求 |
| 统一 CLI `--limit` | `None` | 每渠道本地截取数量；统一入口 `0` 为不截取 |

单次容量：一次 GET 只解析默认页面中的 `div.search-result` 和匹配的表格行。默认输出全部有效匹配，正数限制 L 后至多为 `min(L, 当页解析条数)`；没有请求更多页面或金融数据接口。注册表 `default_limit=None`，未定义 `max_limit`，无硬编码总条数上限。

官方搜索页面默认容量与最大条数：未公布，未检索到可核实的官方容量说明；本实现按一次实际页面决定。社区讨论的分页和金融数据表容量不能用于确认此搜索 URL 的上限。

官方来源与核实范围（2026-10-25）：[集思录用户指引与常见问题](https://app.jisilu.cn/question/420922)、源码使用的官方搜索入口 `https://app.jisilu.cn/search/`。联网检索未找到官方搜索条数承诺，本次未调用搜索入口重新测试。

`jisilu_no_api.py` 通过 `https://app.jisilu.cn/search/?q=...` 读取网页 HTML，继承 `no_api/base_engine.py`。当前解析对象为 `div.search-result` 与 class 包含 row 的表格 `tr`，偏向名称和表格说明的结构；脚本没有调用金融数据 JSON 接口。

函数返回对象数组，`--json` 输出顶层仅为 `{results:array<object>}`。数量上限在基类解析完成后切片；没有保留原生分页、命中总数、查询回显或单独状态字段。

| 字段 | 类型、缺省与条件 | 来源及语义 |
| --- | --- | --- |
| `title` | 非空 string | 第一列 `td[1]` 全部文本或 class 包含 name 的链接文本，连接后 strip |
| `href` | 非空 string | 第一列链接或 name 链接的 `href`，直接连接 |
| `body` | string，缺省 `""` | 第二列文本与 class 包含 info 的 `td` 文本并集，连接后 strip |
| `engine` | string，固定 `jisilu` | 脚本增加的服务标识 |

只有标题和链接同时非空的项目被保留，异常项目被跳过。字段没有正常 null 值；缺少第二列或说明节点时仍可产生 `body:""`。第一列可能含名称、代码或其他展示文字，脚本没有进一步拆分成证券代码、类型、收益率等独立属性；`body` 也只是表格信息或搜索说明，无法保证是普通文章摘要。

链接保持 HTML 原属性，不补全相对地址，不验证 HTTP(S)，不追踪重定向。正文页面从未下载。文本中的日期、价格和比率均保持文本语义，没有类型转换、单位拆分或结构化发布时间；多个匹配节点直接连接还可能削弱原有分隔。图标、列表其他列、讨论作者、互动统计等均不进入这四个字段。

联合入口 `jisilu_direct` 读取脚本 `results` 并原样放入渠道 `items`。它没有进入 `NATIVE_WEB_SCRIPTS` 的标准化路径，链接与内容仍使用 `href/body`，不保证存在 `url/content/published/thumbnail/sources`。联合运行时间属于查询执行元数据，不能用于判定金融信息的新旧。

证据来自当前脚本、共享基类和联合适配代码。`.work/output-analysis/no-api.json` 的真实关键词 `sustainable apparel textile industry` 得到 `success:true`、`items:[]`、`total:0`。这只验证当前调用返回空集合；没有非空字段样本，不能区分实际无匹配与静态选择器未匹配，字段定义仅由源码确认。
