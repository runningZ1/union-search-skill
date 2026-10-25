# 知乎开放平台输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 官方参数正文未取得，上限尚未独立确认；本地限制为站内 10、全网 20、热榜 30 | search/global 默认请求 10，hot 默认请求 30；统一默认调用 search | 每个 scope 一次请求，无页码、游标或自动翻页 | 请求数量先按 scope 夹取，再在统一层截取；统一 `0` 使用搜索默认 10，不能突破本地范围 |

真实站内结果见 [搜索结果样例](examples/search-result.json)。文件为统一 CLI 的 `data.results.zhihu_official` 渠道对象，属于 CLI 渠道对象证据层；条目由 Data.Items 重建，未保存原始 HTTP 响应。容量依据下文已有资料与 COUNT_LIMITS 实现，3 条站内样例不验证 global、hot 或 ask 的返回结构。

## 常用参数与返回数量

资料整理日期：2026-10-25。依据 `zhihu_official_search.py` 与官方文档入口；此次未重新执行搜索、热榜或直答。

| 参数 | 含义 | 默认值或未指定行为 | 范围与实际约束 |
| --- | --- | --- | --- |
| `search/global` 与 `query` | 知乎站内或全网搜索 | query 必填，统一渠道默认 scope=search | query 去除首尾空白后不能为空；统一可传 `scope=global` |
| 搜索 `-m/--max-results` | 发送给 Count 的数量 | CLI 为 `None`，search/global 都发送 `10` | 本地 search 夹取至 `1..10`，global 夹取至 `1..20`；零和负数变为 1，超上限压至上限 |
| `hot -m/--max-results` | 发送给热榜 Limit 的数量 | `None` 转为 `30` | 本地夹取至 `1..30` |
| 统一 `--limit` | 每渠道输出上限 | 未指定或 `0` 解析为 `None`，搜索仍请求 10 | 正整数传给 max-results，再受对应 scope 的夹取限制，返回后另有本地截断；统一渠道不调用 hot/ask |
| `--timeout` | 单次 HTTP 请求超时 | 搜索/热榜为 `10` 秒，ask 为 `60` 秒 | CLI 接受整数；实际网络库验证有效值 |
| `--base-url` | 开放平台地址 | 已有配置或 `https://developer.zhihu.com` | 去除末尾斜线；接口路径保持不变 |
| `--access-secret` | 开放平台认证 | 使用已有 `ZHIHU_ACCESS_SECRET` | 缺少时直接失败；访问权限由账号决定 |
| `ask --model` | 直答模型 | `zhida-agent` | `zhida-fast-1p5/zhida-thinking-1p5/zhida-agent`；返回回答对象，不具有搜索条数参数 |
| `--json` | JSON 输出 | `false` | 布尔开关，不改变数量 |

**本实现每请求数量上限为站内 10、全网 20、热榜 30；官方上限尚未独立确认。** 这些数字可由源码 `COUNT_LIMITS` 明确验证。本次访问官方 `/docs` 仅取得页面标题，未能读取接口参数正文，不能把本地常量直接标为已经核实的官方承诺，也不能用第三方接口或文档副本替代官方证据。

站内、全网与热榜各调用一次对应 GET 接口，没有 page、offset、游标或自动翻页实现。统一 limit 控制单次请求目标并在输出端截断，不能让 search 返回超过本地 10 条或 global 超过 20 条。不指定统一 limit 时仍使用搜索默认 10；不指定热榜数量则使用 30。无 URL 的条目会被本地过滤，实际输出可能少于 Count/Limit；内容可见性、搜索覆盖、热榜实时变化、账号额度与频率限制也影响结果。ask 的回答与引用来源不能据此按搜索条数计数。

官方来源（资料整理日期：2026-10-25）：[知乎开放平台文档](https://developer.zhihu.com/docs)。对应实现路径为 `/api/v1/content/zhihu_search`、`/api/v1/content/global_search`、`/api/v1/content/hot_list`；官方参数正文此次不可读取，默认值与上限的官方证据均待确认。

## 响应层次

覆盖统一渠道 `zhihu_official` 及独立脚本的 `search`、`global`、`hot`、`ask` 输出。搜索类接口的原生响应读取 `Code`、`Message`、`Data.Items`；`Code != 0` 直接失败。模块重建结果对象，没有完整透传原始 `Data`。独立站内/全网搜索的 JSON 为 `{"results": [...]}`；统一渠道默认使用站内搜索，数组进入 `data.items` 或 `data.results.zhihu_official.items`。

## 站内与全网搜索字段

| 模块字段 | 类型 | 原生映射及规则 |
|---|---|---|
| `title` | string | `Title`，空值用 Url；去除首尾空白 |
| `href` | string | `Url`；没有非空地址的条目会被跳过，可能保留服务跟踪参数 |
| `body` | string | `ContentText`，缺失或 null 变为 `""`；属于接口提供的文本，完整程度由服务决定 |
| `engine` | string | 本地常量 `zhihu_official` |
| `author_name` | string | `AuthorName`，缺失或 null 变为 `""` |
| `edit_time` | integer/null，本轮为 integer | `EditTime` 原值，缺失为 null；没有做单位与时区转换，不能直接当作 ISO 日期 |
| `vote_up_count` | 上游数值类型，本轮为 integer | 仅站内搜索：`VoteUpCount`，键缺失补 0，显式 null 保留 |
| `comment_count` | 上游数值类型，本轮为 integer | 仅站内搜索：`CommentCount`，键缺失补 0，显式 null 保留 |
| `scope` | string | 仅全网搜索固定为 `global`，全网不增加上面两项互动计数 |

标题、作者、计数均不会自动提取品牌、面料、服装品类等信息。`edit_time` 描述编辑时间，不应默认解释为首次发布日期。

## 其他独立输出

`hot` 输出 `results` 数组与 `total`；条目含 `title`、`href`、`body`、`engine`、`thumbnail_url`。其中 body 来自 Summary，thumbnail_url 来自 ThumbnailUrl，缺失补空字符串；total 读取 Data.Total，键缺失时用原始条目数，可能与过滤后结果长度不同。

`ask` 从对话响应 `choices[0].message` 提取 `answer`、`reasoning_content`，另外返回 `model`、`id`，均按实现提供空字符串或模型默认值。直答没有搜索结果数组，不能当作站内搜索条目使用。当前统一渠道不暴露热榜和直答结果结构。

## 验证范围

以 `sustainable apparel textile industry` 实测站内搜索返回 3 条，8 个默认条目字段均存在，edit_time 与两项计数为 integer。证据为 `.work/output-analysis/api.json` 的对应渠道。全网、热榜、直答仅依据本目录实现分析，本轮未调用；不对其上游完整响应作保证。
