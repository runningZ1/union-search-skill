# Yahoo 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 网页默认每页容量与最大条数未公布 | `page=1`、`max_results=None`，保留当页全部有效条目；Cookie 偏好 `pn=10` 无足量保证 | 沿 next 链接访问至指定页，只返回该页；无本地页码数值上限，缺失下一页链接时失败 | 正数本地截取指定页，`0` 不截取；不按目标数量汇总多页 |

真实结果见 [搜索结果样例](examples/search-result.json)。文件保存统一 CLI 的 `data.results.yahoo` 渠道对象，属于 CLI 渠道对象证据层；保存标准化条目与执行状态，未保存原始 HTTP HTML 或 Yahoo 包装地址。容量依据下文已有资料，样例 3 条不能作为每页容量上限。

## 常用参数与单次容量

资料核对日期：2026-10-25。参数行为按 `yahoo_search.py`、`yahoo_no_api.py` 与联合入口核对。

| 参数 | 默认值 | 含义与实现范围 |
| --- | --- | --- |
| `query` | 必填 | 编码为网页查询参数 `p` |
| `page` / `--page` | `1` | 正整数，从第一页沿页面 next 链接访问至指定页，只返回该页 |
| `max_results` / `--max-results` | `None` | 指定页解析后本地截取；`0` 也保留整页 |
| `timelimit` / `--timelimit` | `None` | `d/w/m` 表示近一天、一周、一个月，发送 `btf`；`y` 明确不支持 |
| `safesearch` / `--safesearch` | `moderate` | `off/moderate/strict`，在偏好 Cookie 中映射为 `vm=p/i/r` |
| `timeout` / `--timeout` | `20` 秒 | 遍历所有访问页面共用截止时间；统一 CLI 默认 60 秒 |
| `proxy` / `--proxy` | 未显式指定 | 依次取传入值、`YAHOO_PROXY`、`NO_API_KEY_PROXY` |
| 统一 CLI `--limit` | `None` | 每渠道本地上限；`0` 不截取，不因数量要求自动汇总多页 |

单次容量：默认解析第一页所有 `algo-sr` 容器。指定第 P 页时顺序访问 P 个页面，只返回第 P 页，缺少下一页链接直接失败。正数限制 L 后至多输出 `min(L, 指定页有效条数)`。偏好 Cookie 写有 `pn=10`，表示实现发送的偏好值，不能保证实际返回 10 条。`build_search_url()` 对大于 1 的页码有 `pz=7` 与七条步进的构造分支，但实际 `search()` 以第一页 URL 开始并跟随 next 链接，容量不由该分支确定。

官方网页默认每页容量与最大条数：未公布，未核实到固定条数承诺；本实现按一次实际页面决定。注册表 `default_limit=None`，没有 `max_limit`，源码没有固定结果条数或页码数值上限。

官方来源与核实范围（2026-10-25）：[Yahoo SafeSearch 官方帮助](https://in.help.yahoo.com/kb/search-for-desktop/select-setting-yahoo-safesearch-sln2247.html)。官方检索内容确认 Strict、Moderate、Off 三种模式；正文抓取未成功，检索内容未给出固定每页容量。

`yahoo_search.py` 读取 `https://search.yahoo.com/search` 的网页 HTML，从 `div.algo-sr` 提取网页结果。`yahoo_no_api.py` 继承相同搜索类；联合别名 `yahoo_direct` 归并到 `yahoo`，两种入口共用本篇格式说明。分页通过页面的 next 链接继续访问，输出为指定页的结果。

函数返回对象数组。脚本 `--json` 顶层为 `query:string`、`page:integer`、`total_results:integer` 和 `results:array<object>`。条数为当前页经截取后的输出数量，未保留全站命中总数。

| 条目字段 | 类型与缺省 | HTML 来源及处理 |
| --- | --- | --- |
| `title` | 非空 string | `compTitle` 中含 h3 的链接，提取 h3 文本并归整空白 |
| `url`、`href` | 相同的非空 string | 标题链接地址，经 Yahoo 包装地址解析后校验 HTTP(S) |
| `content`、`body` | 相同 string，可为 `""` | 结果容器直接子级 `div.compText` 的文本 |
| `engine` | string，固定 `yahoo` | 本地渠道标识 |

如果链接域名为 `r.search.yahoo.com`，脚本查找路径中唯一的 `RU=` 段并 URL 解码得到目标；缺少唯一目标会失败。其他域名原样使用，没有追加落点网络请求。标题链接缺失、标题为空、目标非法或整页没有识别结果都会失败。说明缺失时仍可返回空字符串。

`content` 来自搜索摘要，可能带日期、站点说明或省略号，没有读取目标正文。日期保持文本语义，时间筛选参数不映射为条目时间。站点图标、排名、缩略图和丰富结果属性没有单独保留。

联合适配读取 `results` 并标准化为 `title/url/content/published/thumbnail/sources`，去除兼容副本；`published` 与 `thumbnail` 缺省为 null。来源平台和 engine 均为 `yahoo`，rank 从有效返回顺序的 1 开始。URL 进一步删除 fragment 与已知跟踪参数。只有完全由结构化网页渠道组成的聚合批次通过 `merge_items()` 增加 `id` 并按需合并来源，混合批次不保证相同形状。

证据来自两个 Yahoo 脚本、`web_search.py` 和联合标准化代码。`.work/output-analysis/no-api.json` 的真实查询成功返回 3 条，首条 ScienceDirect 文章摘要以 `Jun 1, 2024` 开头，但 `published:null`。实测确认了标准化字段与日期仍在摘要中的行为；原始包装地址未单独保存，RU 解析规则由源码确认。
