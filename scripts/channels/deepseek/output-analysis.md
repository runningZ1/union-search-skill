# DeepSeek 输出结果分析

覆盖 `deepseek_search.py` 的客户端、`search_deepseek`、`--json` 和 `union_search.py::_search_deepseek`。正常请求访问 `/v1/tools/search`，源码要求 HTTP 200 且顶层 `results` 为数组。

## 原始路径与模块字段

模块逐项读取服务 `results[]`，构造以下完整字段集合；脚本包装成 `results` 对象。表中类型区分实测与源码默认规则。

| 模块字段 | 来源、类型与缺失规则 |
| --- | --- |
| title | string；title 或 url，去除两端空白 |
| href | string；url 去除空白；空地址条目跳过 |
| body | string；snippet 优先，其次 summary，最后空字符串 |
| engine | string；固定 deepseek |
| summary | 实测 string；summary 缺失为空字符串，显式 null 保留 |
| content | 实测 string；content 缺失为空字符串，显式 null 保留 |
| site_name、site_icon、date | 实测 string；上游同名字段，缺失为 null |
| authority | 实测 integer；原值保留，缺失为 null |
| rerank_score | 实测 number；原值保留，缺失为 null |

请求 `need_content` 默认 false；content 的存在不能直接证明拿到了完整正文，应检查实际内容。body 不会截断，summary/content 也不做清洗或长度限制。date 未进行格式和时区解析。终端把 rerank_score 标注为相关度，但源码没有定义范围、方向、归一化方式；authority 的枚举及强弱关系也未验证，不能依据名称确定阈值。

## 丢弃规则与统一 CLI

其他上游条目字段和顶层响应元数据未保留。模块遍历全部 results，adapter 再执行结果上限切片；缺失或非数组 results 直接失败，不生成正常空结果。空 url 被丢弃，title 缺失时用地址补充。

统一 CLI 保留模块条目字段：单渠道路径是 `data.items[]`，联合搜索是 `data.results.deepseek.items[]`，联合 `data.final_items[]` 增加 `_source_platform`。外层 `ok/errors/meta` 与渠道 `success/total` 为执行信息，不是服务原始 JSON。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| 50 条 | `max_results=None` 时请求 `count=10` | 官方未公布分页参数；模块只请求一次 | 不指定或 0 时仍请求 10；正数发送为 `count` 并本地切片，超过 50 在模块校验处失败 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[Search API](https://api-docs.deepseek.com/zh-cn/api/search/)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `query` | 必填查询，官方 1—128 个 Unicode 字符；模块也检查非空与最多 128 字符 |
| `max_results` → `count` | 模块默认 `None` 时实际请求 10；官方默认 10，范围 1—50，模块显式值同范围校验 |
| `ori_question` | 原始问题，可选；官方 1—128 字符，模块默认不发送 |
| `localization` | 用于本地结果优先的 IP 地址，模块默认不发送；官方默认空字符串 |
| `need_content` | 是否获取正文，官方与模块默认 false；官方说明 false 时 content 为空 |
| `timeout` | 模块 HTTP 超时，默认 30 秒 |

官方单次最多 50 条，当前文档未公布分页参数。统一 CLI `--limit` 默认不指定、0 表示不额外截断，此时仍请求 10；正数传入 `count`，大于 50 会在模块校验处失败。模块只请求一次并过滤空地址，adapter 另做本地切片；设置数量不保证实际匹配结果达到该数量。

## 证据范围

已核对本目录实现、对应 adapter 及 `.work/output-analysis/api.json` 的三条成功结果；上述实测类型来自处理后的条目。未保存完整原始 HTTP 响应，无法枚举服务额外字段；正文模式、本地化参数及分数边界未实测。
