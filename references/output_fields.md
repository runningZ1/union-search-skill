# 搜索输出字段文档索引

文档按服务目录归档，同一服务的 API、网页直连和兼容名称在同一篇中分节说明。范围包含统一注册表的 52 个搜索入口、微信和 RSS 独立搜索；图片下载、媒体下载与正文提取有各自契约，不属于本次关键词搜索字段分析。

各服务文档统一命名为 `output-analysis.md`，正文使用中文。各篇区分上游响应、模块保留字段与统一 CLI 输出，注明类型、来源映射、缺失规则和实测范围，并说明常用参数、默认值和单次结果容量。

容量说明分别记录官方单次请求上限、当前实现的请求数量、分页行为和本地结果上限。官方没有公开固定数量时明确注明，不将 `--limit 0` 视为无限搜索，也不把单次三条实测结果视为渠道容量。官方来源和核查日期保存在各服务文档中。结构说明来自当前实现；实测中没有出现的可选字段不代表已经验证。原始响应中未经本模块读取的字段，不视为稳定承诺。

## 渠道目录中的留样

有效结果保存在对应服务目录的 `examples/`，与 `output-analysis.md` 一起归档。

| 文件 | 内容 |
|---|---|
| `examples/search-result.json` | 当前服务的一份真实非空成功结果；统一入口渠道保存完整渠道对象，微信与 RSS 等保留独立入口结构 |
| `examples/search-result-<入口>.json` | 同一服务其他成功入口的额外样例，例如 API 与网页直连、不同账号后端 |
| `examples/search-result-info.json` | 主样例的查询、来源文件、采集时间（原记录提供时）和数据层次说明 |
| `examples/search-result-<入口>-info.json` | 额外样例对应的来源说明 |

JSON 从实际调用结果中提取，保留原有字段和值；不是原始 HTTP 响应的渠道不会标记为原始响应。归档前检查不含已配置密钥。没有非空成功响应的渠道仅记录缺口，不提供虚构的正常样例。当前 35 个服务目录共有 40 份有效结果文件及各自说明文件，兼容名称共用来源样例。

## 常用参数的共同含义

| 参数 | 作用与数量边界 |
|---|---|
| `query` | 查询关键词；部分 AI 服务还支持独立 objective，指定搜索目标 |
| `--limit N` | 每渠道保留上限；不同适配器可能将它传给上游或取得响应后截断，应查看服务文档 |
| `--limit 0` | 不做本地条数限制，仍受单页、请求批量、模型输出和超时限制 |
| `--preset small/medium/large/extra` | 联合入口数量预设，分别对应 3/5/10/20 条 |
| `--timeout` | 执行时间预算，具体服务可能有更小的参数上限 |
| `--param key=value` | 单渠道参数透传，可重复使用；服务支持的字段见各篇，不保证独立脚本的所有参数均可透传 |
| `--deduplicate` | 联合结果按地址去重，处理后条数可能减少 |
| `--max-workers` | 并发渠道数，不改变服务单次结果容量 |

“官方单次上限”是一个服务请求的容量；“模块一次调用”可能包含分页或详情补充请求；“返回条数”还受过滤、去重和本地 limit 影响。这些数量分别记录，不能互相代替。文档引用的官方容量也不代表当前账号已开通对应套餐。

## 商业 API 与同服务网页入口

| 服务目录 | 字段文档 |
|---|---|
| AnySearch | [输出结果分析](../scripts/channels/anysearch/output-analysis.md) |
| 百度千帆、百度网页 | [输出结果分析](../scripts/channels/baidu/output-analysis.md) |
| 百炼 | [输出结果分析](../scripts/channels/bailian/output-analysis.md) |
| Bing SerpAPI、中国与国际网页 | [输出结果分析](../scripts/channels/bing/output-analysis.md) |
| DeepSeek | [输出结果分析](../scripts/channels/deepseek/output-analysis.md) |
| Exa | [输出结果分析](../scripts/channels/exa/output-analysis.md) |
| Firecrawl | [输出结果分析](../scripts/channels/firecrawl/output-analysis.md) |
| Google API、网页与香港网页 | [输出结果分析](../scripts/channels/google_search/output-analysis.md) |
| Jina | [输出结果分析](../scripts/channels/jina/output-analysis.md) |
| Kimi | [输出结果分析](../scripts/channels/kimi/output-analysis.md) |
| 秘塔 | [输出结果分析](../scripts/channels/metaso/output-analysis.md) |
| Ollama | [输出结果分析](../scripts/channels/ollama_search/output-analysis.md) |
| Parallel | [输出结果分析](../scripts/channels/parallel_search/output-analysis.md) |
| Serper | [输出结果分析](../scripts/channels/serper/output-analysis.md) |
| Tavily | [输出结果分析](../scripts/channels/tavily_search/output-analysis.md) |
| TinyFish | [输出结果分析](../scripts/channels/tinyfish/output-analysis.md) |
| 火山引擎 | [输出结果分析](../scripts/channels/volcengine/output-analysis.md) |
| Yandex SerpAPI 与网页 | [输出结果分析](../scripts/channels/yandex/output-analysis.md) |
| 腾讯元宝 | [输出结果分析](../scripts/channels/yuanbao/output-analysis.md) |
| 智谱 | [输出结果分析](../scripts/channels/zhipu/output-analysis.md) |

## 网页与即时答案

| 服务目录 | 字段文档 |
|---|---|
| Brave 与兼容入口 | [输出结果分析](../scripts/channels/brave/output-analysis.md) |
| DuckDuckGo 网页与兼容入口 | [输出结果分析](../scripts/channels/duckduckgo/output-analysis.md) |
| DuckDuckGo 即时答案 | [输出结果分析](../scripts/channels/duckduckgo_instant/output-analysis.md) |
| Ecosia | [输出结果分析](../scripts/channels/ecosia/output-analysis.md) |
| 集思录 | [输出结果分析](../scripts/channels/jisilu/output-analysis.md) |
| Mojeek | [输出结果分析](../scripts/channels/mojeek/output-analysis.md) |
| Qwant | [输出结果分析](../scripts/channels/qwant/output-analysis.md) |
| 夸克 | [输出结果分析](../scripts/channels/quark/output-analysis.md) |
| 360 | [输出结果分析](../scripts/channels/so360/output-analysis.md) |
| 搜狗 | [输出结果分析](../scripts/channels/sogou/output-analysis.md) |
| Startpage | [输出结果分析](../scripts/channels/startpage/output-analysis.md) |
| 头条 | [输出结果分析](../scripts/channels/toutiao/output-analysis.md) |
| WolframAlpha | [输出结果分析](../scripts/channels/wolfram/output-analysis.md) |
| Yahoo 与兼容入口 | [输出结果分析](../scripts/channels/yahoo/output-analysis.md) |
| 网页公共规范化与信封 | [输出结果分析](../scripts/channels/no_api/output-analysis.md) |

## 平台、账号与独立入口

| 服务目录 | 字段文档 |
|---|---|
| GitHub | [输出结果分析](../scripts/channels/github_search/output-analysis.md) |
| Reddit | [输出结果分析](../scripts/channels/reddit/output-analysis.md) |
| YouTube | [输出结果分析](../scripts/channels/youtube/output-analysis.md) |
| 小宇宙 FM | [输出结果分析](../scripts/channels/xiaoyuzhoufm/output-analysis.md) |
| Wikipedia | [输出结果分析](../scripts/channels/wikipedia/output-analysis.md) |
| 知乎开放平台 | [输出结果分析](../scripts/channels/zhihu_official/output-analysis.md) |
| 本机账号搜索的三个后端 | [输出结果分析](../scripts/channels/ai_tools/output-analysis.md) |
| 微信公众号 | [输出结果分析](../scripts/channels/wechat/output-analysis.md) |
| RSS | [输出结果分析](../scripts/channels/rss_search/output-analysis.md) |

## 实测证据

本轮查询以 `sustainable apparel textile industry` 为共同关键词，每渠道最多 3 条；微信查询 `服装行业`，RSS 从真实 Guardian Fashion 订阅源查询 `fashion`，即时答案补充查询 `textile`。本机账号后端使用其文档注明的同类查询。

- `.work/output-analysis/api.json`：23 个 API 渠道全部返回 3 条，共 69 条。
- `.work/output-analysis/no-api.json`：26 个无必填 API Key 入口按兼容来源合并后执行 23 个来源；10 个来源返回结果，9 个正常结束但零条，4 个失败。
- `.work/output-analysis/duckduckgo-instant-textile.json`：即时答案补充查询返回 3 条。
- `.work/output-analysis/sample-recheck.json`：使用 `服装` 补查缺少样例的入口，百度网页直连返回 3 条；其他八个入口仍为零条。
- `.work/output-analysis/wechat.json`、`rss.json`：两个独立入口均取得 3 条。
- `.work/output-analysis/ai-tools.json`：三个本机账号后端均成功返回 3 条，共 9 条。

上述任务文件为本地实测记录，受 `.gitignore` 排除，不作为文档链接的分发依赖。各篇中的字段类型以源码行为和已观察值共同说明，单次类型不限制上游未来变化。共同关键词命中同一篇文章时不构成独立来源。本文及各服务文档只分析输出结构，不实现后续筛选逻辑。
