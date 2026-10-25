# 夸克输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 网页每页默认容量与最大条数未公布 | `page=1`、`max_results=None`，保留受支持卡片展开后的全部有效条目；注册表 `default_limit=None` | 指定正整数页码，每次只请求该页，无本地页码数值上限 | 正数在卡片展开后本地截取，`0` 不截取；不触发下一页 |

真实结果见 [搜索结果样例](examples/search-result.json)。文件保存统一 CLI 的 `data.results.quark_direct` 渠道对象，包含标准化后的条目，属于 CLI 渠道对象证据层；原始 HTTP HTML 与内嵌卡片 JSON 未保存，卡片类别映射依据源码。容量依据下文已有资料，3 条样例不能作为每页容量上限。

## 常用参数与单次容量

资料核对日期：2026-10-25。参数行为来自 `quark_no_api.py`、共享校验函数和联合入口。

| 参数 | 默认值 | 含义与实现范围 |
| --- | --- | --- |
| `query` | 必填 | 不得全为空白，发送为 `q` |
| `page` / `--page` | `1` | 正整数，直接发送 `page`，一次只取指定页 |
| `max_results` / `--max-results` | `None` | 卡片展开后本地截取；`0` 也保留全部解析结果 |
| `timeout` / `--timeout` | `20` 秒 | 搜索请求截止时间；统一 CLI 默认 60 秒 |
| `proxy` / `--proxy` | 未显式指定 | 使用传入代理或共享 Session 的 `NO_API_KEY_PROXY` |
| `layout` | 固定 `html` | 请求 HTML 页面，不提供修改入口 |
| 统一 CLI `--limit` | `None` | 每渠道本地上限；`0` 不截取，不触发自动翻页 |

单次容量：只请求一次指定页 HTML，默认返回其中受支持卡片展开后的全部条目。一张 `news_uchq` 或 `ai_page` 卡片可产生多个结果，网页卡片数与输出条数没有一一对应关系。正数限制 L 后至多返回 `min(L, 卡片展开后的有效条数)`。注册表 `default_limit=None`，未定义 `max_limit`，源码没有页码数值上限或总条数上限；不自动请求后续页。

官方网页每页默认容量与最大条数：未公布；本实现按一次实际页面决定。官方浏览器帮助说明搜索操作，未说明 `quark.sm.cn/s` 的固定条数或分页容量。

官方来源（2026-10-25）：[夸克帮助：快速开始](https://www.quark.cn/documents/help/get-started)，已读取正文，确认通过搜索框或地址栏输入查询打开搜索结果，未发现条数限制说明。

`quark_no_api.py` 访问 `https://quark.sm.cn/s` 的 HTML，读取 `script[type="application/json"]` 且 id 以 `s-data-` 开头、`data-used-by="hydrate"` 的内嵌 JSON。卡片类别来自 `extraData.sc`，数据来自 `data.initialData`。来源属于网页内嵌匿名 JSON，没有单独调用搜索 JSON API。函数返回对象数组，脚本 JSON 顶层只有 `results:array<object>`。

| 原生卡片或字段 | 标题、URL、说明的映射 |
| --- | --- |
| `ss_doc/ss_kv/ss_text/baike/structure_web_novel` | 有 `titleProps` 时取 `titleProps.content/sourceProps.dest_url/summaryProps.content`；有 `normal_url` 时取 `title/normal_url/show_body`；其他取 `title/url/desc`，desc 缺省再取 text |
| `nature_result` | `title/url/desc` |
| `addition` | `title.content/source.url/summary.content` |
| `ss_note` | `title.content/source.dest_url/summary.content` |
| `baike_sc` | 从内层 `data` 取 `title/url/abstract` |
| `news_uchq` | 遍历 `feed`，取 `title/url/summary` |
| `ai_page` | 遍历 `list`，取 `title/url/content`；content 为列表时用 ` | ` 连接 |

输出字段为非空 `title:string`、相同的 `url/href:string`、相同的 `content/body:string`、固定 `engine:"quark"` 与 `category:string`。说明缺省为空字符串，null 或空说明经 `_plain()` 也成为空字符串；标题和说明先去 HTML 并归整空白，地址必须为绝对 HTTP(S)。卡片必需键缺失会失败；未支持的 category 不生成条目，一张 feed 卡片可生成多个条目。

说明可能为论文关键词、百科介绍、新闻摘要或 AI 卡片文本，不能统一视为正文。日期、来源站名若混在说明内不会拆分；图片、卡片层级、统计、完整 feed 元数据均不保留。URL 直接使用卡片目标属性，不请求目标正文或跟踪落点。

联合平台 `quark_direct` 执行标准化：保留 `title/url/content`，丢弃 `href/body/category`，补充 `published:null`、`thumbnail:null` 和 `sources:[{platform:"quark_direct",engine:"quark",rank:integer}]`。URL 清理 fragment 与已知跟踪字段；全结构化网页聚合可增加 `id` 并合并同 URL 来源。后续需要按卡片类别筛选时，当前联合输出已无法恢复 category。

证据为该脚本、`web_search.py` 与联合标准化代码。`.work/output-analysis/no-api.json` 中真实查询成功返回 3 条，首条为中国科学院知识服务平台的图书页面，说明包含主题词、语种和数据库名称；第二条说明含 AI 功能文字，显示内容并非纯文章摘要。实测文件只留有标准化字段，具体卡片类别仅能由源码确认。
