# 搜狗输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 帮助列出每页 10、20、30、50、100 条，100 为最大设置选项；当前默认与绝对上限未公布 | `page=1`、`max_results=None`，保留当页筛选去重后的全部有效条目，未发送每页条数设置 | 可指定正整数页码，一次只取指定页，无本地页码数值上限 | 正数本地截取，不能启用网页每页 100 条；`0` 不截取，不自动翻页 |

真实结果见 [搜索结果样例](examples/search-result.json)。文件为统一 CLI 的 `data.results.sogou_direct` 渠道对象，属于 CLI 渠道对象证据层；保存标准化条目，未保存原始 HTTP HTML 或标题链接属性。容量依据下文已有资料，样例 3 条仅用于核对字段和值。

## 常用参数与单次容量

资料核对日期：2026-10-25。参数默认值来自 `sogou_no_api.py` 与联合入口。

| 参数 | 默认值 | 含义与实现范围 |
| --- | --- | --- |
| `query` | 必填 | 不得全为空白，发送为 `query` |
| `page` / `--page` | `1` | 正整数，发送为 `page`，只请求指定页 |
| `max_results` / `--max-results` | `None` | 解析及 URL 去重后本地截取；`0` 也保留整页 |
| `timelimit` / `--timelimit` | `None` | `d/w/m/y` 为近一天、一周、一个月、一年，映射为 `s_from=inttime_day/week/month/year` 并发送 `tsn=1` |
| `timeout` / `--timeout` | `15` 秒 | 页面请求超时；统一 CLI 默认 60 秒 |
| `proxy` / `--proxy` | 未显式指定 | 传入代理或共享 Session 的 `NO_API_KEY_PROXY` |
| 统一 CLI `--limit` | `None` | 每渠道本地条数上限；`0` 不截取，不触发翻页 |

官方高级搜索帮助列出每页 10、20、30、50、100 条结果选项；100 是文档列出的最大设置值。该页没有给出默认值，也未承诺所有查询均返回相应数量或将 100 定义为所有网页情形下的绝对上限。当前接口默认页面的固定容量与官方绝对上限未公布。

单次容量：实现只进行一次指定页 GET，未发送每页条数设置，默认保留当页经筛选和去重后的全部可识别结果。`max_results=100` 只执行本地截取，不启用网页 100 条设置；正数限制 L 后至多为 `min(L, 当页有效条数)`。注册表 `default_limit=None`，没有 `max_limit`，源码没有固定结果条数或页码数值上限。本实现的实际容量由一次页面决定。

官方来源（2026-10-25）：[搜狗高级搜索帮助](https://help.sogou.com/advanced.html?v=1)，已读取正文并核对每页选项；[搜狗更多功能](https://www.sogou.com/docs/features.htm)，官方检索内容说明可通过个性设置调整每页数量。

`sogou_no_api.py` 读取 `https://www.sogou.com/web` 的 HTML，在 class 为 rb 或 vrwrap 的 `div` 中提取结果。使用 `web_search.py` 的网页工具；`base_engine.py` 的旧返回约定不决定本渠道字段。函数返回数组，`--json` 顶层为 `{results:array<object>}`，没有全站命中数。

| 输出字段 | 类型与缺省 | 来源与处理 |
| --- | --- | --- |
| `title` | 非空 string | 首条 `h3/a` 文本，合并空白 |
| `url`、`href` | 相同的非空 string | 标题链接 href；若路径为 `/link`，优先标题自身 data-url，再取容器首个 data-url |
| `content`、`body` | 相同 string，可为 `""` | 合并指定摘要区域的文本 |
| `engine` | string，固定 `sogou` | 本地标识 |

目标链接基于 `https://www.sogou.com/` 补全相对路径，检查 HTTP(S)，按相同目标地址去重。标题为空、缺链接或协议不符的结果跳过。摘要类名包括 ft、attribute-centent、fz-mid、star-wiki、vr-info、str_info；嵌套匹配时保留外层，避免重复合并。摘要可以没有任何匹配节点，输出空字符串。

存在 data-url 时可得到目标地址；否则 `/link` 跳转地址可能保留，脚本不请求跳转落点，也不设置 `link_type`。因此联合结果没有 redirect 标记并不保证地址已经解析。标题与摘要均来自搜索页，未提取文章全文。日期、站点名若属于摘要区域则混在说明中；没有单独的发布时间或作者字段。时间筛选是请求参数，与条目 `published` 无映射。广告和丰富卡片属性也未结构化保留。

联合入口 `sogou_direct` 标准化为 `title/url/content/published/thumbnail/sources`，去除兼容副本，时间和图片缺省为 null。`sources` 中 platform 为 `sogou_direct`、engine 为 `sogou`，rank 按有效结果的返回顺序从 1 生成。URL 清理 fragment 与已知跟踪参数；全部采用结构化网页渠道的聚合结果增加 `id`，按设置合并同 URL 的来源。

证据为脚本、`web_search.py` 和联合标准化代码。`.work/output-analysis/no-api.json` 中真实服装关键词查询成功返回 3 条，首条为 ResearchGate 上关于服装供应链的论文，`content:""`。这证实缺失摘要的条目仍可正常返回；实测保存的是标准化条目，标题链接原始属性未单独保存。
