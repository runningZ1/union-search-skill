# 今日头条输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 网页默认容量与最大条数未公布，未取得官方数值证据 | `max_results=None`，保留默认页全部有效匹配；注册表 `default_limit=None` | 单次 GET，不支持分页、游标或动态加载 | 正数仅本地截取；统一 `--limit 0` 不截取，独立 `--max-results 0` 返回空数组 |

尚无有效结果留样。已有查询及 `.work/output-analysis/sample-recheck.json` 中查询 `服装` 的 `toutiao_direct` 均为空结果。证据层为 CLI 渠道对象，空集合仅能核对执行状态，非空业务字段依据源码；未保存原始 HTTP 响应。容量依据下文已有资料，公共字段边界见 [公共输出结构](../no_api/output-analysis.md)。

## 常用参数与单次容量

资料核对日期：2026-10-25。默认值来自 `toutiao_no_api.py`、共享基类与联合入口。

| 参数 | 默认值 | 含义与实现范围 |
| --- | --- | --- |
| `query` | 必填 | 编码为搜索 URL 参数 `keyword` |
| `max_results` / `--max-results` | `None` | 完成 HTML 解析后本地切片；独立脚本传 `0` 返回空数组 |
| `timeout` | `15` 秒 | 基类请求超时，独立 CLI 没有该选项；统一 CLI 默认 60 秒 |
| `proxy` / `--proxy` | 未显式指定 | 优先传入代理，其次 `NO_API_KEY_PROXY` |
| `page`、游标、时间、内容类别 | 未提供 | URL 只传查询词；额外关键字不改变 URL，不实现翻页和分类筛选 |
| 统一 CLI `--limit` | `None` | 每渠道本地上限；统一入口 `0` 表示不截取 |

单次容量：只请求一次默认搜索页 HTML，默认保留所有通过标题和链接检查的匹配容器；正数限制 L 后至多为 `min(L, 当页解析条数)`。没有浏览器执行、动态加载、下一页请求或 JSON 接口调用。注册表 `default_limit=None`，未定义 `max_limit`，无固定结果条数上限。

官方网页默认容量与最大条数：未公布，联网检索未找到可核实的官方固定条数说明；本实现按一次实际页面决定。动态网页在浏览器内继续加载的数量不构成此静态请求的可用容量。

官方来源与核实范围（2026-10-25）：官方产品入口 [今日头条](https://www.toutiao.com/)，源码使用 `https://www.toutiao.com/search/?keyword=...`。本次只检索官方容量资料，未重新调用搜索服务，未找到可引用的官方条数承诺。

`toutiao_no_api.py` 请求 `https://www.toutiao.com/search/?keyword=...`，来源为网页 HTML。它继承 `base_engine.py` 并用 lxml 解析响应，未调用头条匿名 JSON 接口或浏览器执行后的内容。匹配容器为 class 包含 article 或 result 的 `div`。

函数返回 `list[dict]`，独立命令 `--json` 输出 `{results:array<object>}`。顶层没有分页游标、查询回显、命中总数或新闻专用元数据。数组在基类解析完成后按 `max_results` 截取。

| 字段 | 类型与缺省 | 来源及语义 |
| --- | --- | --- |
| `title` | 非空 string | `h3` 或 class 包含 title 的链接内全部文本，连接后 strip |
| `href` | 非空 string | `h3 a` 或标题链接的 href 属性，直接连接 |
| `body` | string，可为 `""` | class 包含 abstract 的 `p` 或 class 包含 desc 的 `div` 文本 |
| `engine` | string，固定 `toutiao` | 脚本补充 |

标题和链接必须同时存在且非空，缺失者不输出。摘要节点缺失时生成空字符串；单个容器解析异常被跳过。多个文本节点直接连接，代码没有主动插入分隔符或清理内部空白。正常条目没有 null 字段。

`href` 保留网页原始属性，未补全相对路径、验证 HTTP(S)、解析内容标识或跟踪跳转，因此不能保证是最终文章绝对地址。`body` 只是结果页摘要或描述，没有访问正文。脚本也没有根据文章、视频等内容类别提供独立类型字段；作者、发布时间、阅读量、评论数、封面、视频时长等没有单独保留。摘要里若出现相对时间或日期，只是文本，不会转成时间对象，联合查询执行时间与文章时间无关。

联合入口 `toutiao_direct` 使用通用脚本适配，把顶层 `results` 放入渠道 `items`，继续保留 `title/href/body/engine`。它不属于 `NATIVE_WEB_SCRIPTS`，所以不会自动执行 `normalize_item()`，不能假定有 `url/content/published/thumbnail/sources`，筛选应以现有四字段能力为边界。

证据为本脚本、`base_engine.py`、`web_search.py` 与联合适配代码。`.work/output-analysis/no-api.json` 中真实关键词 `sustainable apparel textile industry` 返回 `success:true`、`items:[]`、`total:0`。这只验证脚本调用完成，没有可核对的非空条目；字段格式来自源码，空数组不能证明头条服务没有相关内容或页面静态选择器有效。
