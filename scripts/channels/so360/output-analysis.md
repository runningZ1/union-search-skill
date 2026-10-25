# 360 搜索输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 网页默认每页条数与最大条数未公布 | `page=1`、`max_results=None`，保留第二次 GET 对应页面的有效去重条目；注册表 `default_limit=None` | 可指定正整数页码；两次 GET 访问同一页，只解析第二次响应，不累计多页 | 正数本地截取，`0` 不截取；无每页条数请求参数，不自动翻页 |

真实结果见 [搜索结果样例](examples/search-result.json)。文件为统一 CLI 的 `data.results.so360_direct` 渠道对象，属于 CLI 渠道对象证据层，保存适配后的条目和执行状态；未保存原始 HTTP HTML，链接属性选择依据源码。容量依据下文已有资料，样例 3 条不表示单页上限。

## 常用参数与单次容量

资料核对日期：2026-10-25。默认值来自 `so360_no_api.py`、共享校验函数和联合入口。

| 参数 | 默认值 | 含义与实现范围 |
| --- | --- | --- |
| `query` | 必填 | 不得全为空白，发送为 `q` |
| `page` / `--page` | `1` | 正整数，发送为 `pn`，只返回指定页 |
| `max_results` / `--max-results` | `None` | 解析并去重后本地截取；`0` 也保留全部结果 |
| `timelimit` / `--timelimit` | `None` | `d/w/m/y` 为近一天、一周、一个月、一年，发送为 `adv_t` |
| `timeout` / `--timeout` | `15` 秒 | 两次页面访问共用截止时间；统一 CLI 默认 60 秒 |
| `proxy` / `--proxy` | 未显式指定 | 传入代理或共享 Session 的 `NO_API_KEY_PROXY` |
| 统一 CLI `--limit` | `None` | 每渠道本地上限；`0` 不截取，不自动翻页 |

单次容量：同一 Session 对同一搜索 URL 进行两次 GET，第一次用于保存 Cookie，只解析第二次返回的指定页。两次访问不累加结果。默认输出该页经协议校验、频道排除和 URL 去重后的全部条目；正数限制 L 后至多为 `min(L, 当页有效条数)`。注册表 `default_limit=None`，未定义 `max_limit`，源码没有页码数值上限、条数上限或每页条数请求参数。

官方网页默认每页条数与最大条数：未公布；本实现按一次实际页面决定。官方帮助描述网页搜索的操作与结果页，未承诺固定条数。

官方来源（2026-10-25）：[360 搜索网页搜索帮助](https://www.so.com/help/help_2_6.html)，已读取正文，未发现固定容量说明。

`so360_no_api.py` 请求 `https://www.so.com/s` 的网页 HTML，使用相同 Session 两次访问后解析 `li.res-list`。本渠道使用 `no_api/web_search.py` 的请求、文档与结果工具，未继承旧 `base_engine.py`。函数返回对象数组；独立 `--json` 命令顶层为 `{results:array<object>}`，没有原生总命中数或分页数据。

| 输出字段 | 类型与缺省 | 来源及语义 |
| --- | --- | --- |
| `title` | 非空 string | 第一条 `h3/a` 的文本，归整空白 |
| `url`、`href` | 相同的非空 string | 优先标题链接 `data-mdurl`，其次 `href`，相对地址基于 `https://www.so.com/` 补全 |
| `content`、`body` | 相同的 string，可为 `""` | 摘要节点合并后归整空白 |
| `engine` | string，固定 `so360` | 本地渠道标识 |

摘要范围为 `data-result-summary`、`p.res-desc`、`span.res-list-summary`、`div.mh-desc`，嵌套匹配时保留内部摘要，避免重复。只接收 HTTP(S) 地址；同一页内按目标地址去重，并排除 ai/video/image/news.so.com 和文库搜索入口。没有标题链接的容器会被跳过。完全没有条目时，只有检测到无结果提示才正常返回空数组，否则失败。

`data-mdurl` 可提供目标地址；缺省使用的 href 仍可能是搜索服务跳转地址，代码没有继续跟踪，也不输出 `link_type`。内容仅来自搜索结果页，没有下载目标全文。日期或来源若包含在摘要中，会原样进入说明；无单独发布时间、缩略图、排名或广告字段。时间筛选参数只约束请求，不生成条目的时间值。

联合入口 `so360_direct` 进入原生网页标准化：使用 `title/url/content`，兼容字段 `href/body` 不保留，增加 `published:null`、`thumbnail:null` 和 `sources`，其中 `platform:"so360_direct"`、`engine:"so360"`、`rank` 为从 1 开始的返回次序。标准化 URL 删除 fragment 与已知跟踪参数；仅结构化网页渠道组成的聚合结果可增加 `id` 并按 URL 合并来源。

证据来自脚本、共享网页工具和联合适配代码。`.work/output-analysis/no-api.json` 的真实查询 `sustainable apparel textile industry` 成功返回 3 条，首条标题为 Mergü Textile – Sustainable Apparel Production，地址为 `https://mergu.com/`，说明包含联系方式及生产介绍。实测确认了标准化字段和摘要内容，HTML 原页没有单独保存，具体链接属性选择来自源码。
