# Wolfram Alpha 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 网页展示区域默认数量与最大数量未公布 | `max_results=None`，保留默认页中说明非空的匹配区域；注册表 `default_limit=None` | 单次 GET，不支持分页、动态执行或计算 API 扩展 | 正数仅本地截取展示区域；统一 `--limit 0` 不截取，独立 `--max-results 0` 返回空数组 |

尚无有效结果留样。已有查询及 `.work/output-analysis/sample-recheck.json` 中查询 `服装` 的 `wolfram_direct` 均为空结果。证据层为 CLI 渠道对象，不能由空集合判断计算服务是否存在答案；非空字段依据源码，未保存原始 HTTP 响应。容量依据下文已有资料，公共字段边界见 [公共输出结构](../no_api/output-analysis.md)。

## 常用参数与单次容量

资料核对日期：2026-10-25。参数默认值来自 `wolfram_no_api.py`、共享基类和联合入口。

| 参数 | 默认值 | 含义与实现范围 |
| --- | --- | --- |
| `query` | 必填 | 计算问题或查询词，编码为网页输入参数 `i` |
| `max_results` / `--max-results` | `None` | 对解析出的展示区域进行本地切片；独立脚本传 `0` 返回空数组 |
| `timeout` | `15` 秒 | 基类请求超时，独立 CLI 未提供此选项；统一 CLI 默认 60 秒 |
| `proxy` / `--proxy` | 未显式指定 | 优先传入代理，其次 `NO_API_KEY_PROXY` |
| `page`、pod 选择、计算假设 | 未提供 | URL 只包含输入问题，不实现分页或计算 API 的参数 |
| 统一 CLI `--limit` | `None` | 每渠道本地数量上限；统一入口 `0` 表示不截取 |

单次容量：一次 GET 读取输入页面，默认保留所有匹配容器中 `body` 非空的展示区域；正数限制 L 后至多为 `min(L, 实际解析区域数)`。没有动态执行或额外计算 API 请求。官方说明每个带标签的展示部分称为 pod，pod 可以包含 subpod；当前宽泛 HTML 选择器没有按原生 pod 标识去重，因此输出数量也不能保证等于计算服务的 pod 数量。注册表 `default_limit=None`，没有 `max_limit` 或固定数量上限。

官方网页展示区域默认数量与最大数量：未公布；本实现按一次实际页面决定。官方 FAQ 提到每次查询有计算时间限制，未给出固定的结果区域数量；计算 API 的配额与响应参数不用于推断本网页模块容量。

官方来源（2026-10-25）：[Wolfram Alpha FAQ](https://www.wolframalpha.com/faqs/)，已读取正文并核对 pod/subpod 的说明，未发现固定数量承诺。

`wolfram_no_api.py` 请求 `https://www.wolframalpha.com/input?i=...` 的网页 HTML，继承共享 `base_engine.py`。它未调用 Wolfram 官方计算 API，没有读取完整的计算响应 JSON，也不执行动态页面脚本。解析容器为 class 包含 result 或 pod 的 `div`，同页可能有多个知识展示区域。

函数返回对象数组；独立 `--json` 顶层为 `{results:array<object>}`。数组截取代表本次保留的展示区域数量，没有原生总命中数、计算成功状态、查询解释或分页信息。

| 字段 | 类型、缺省及条件 | HTML 来源及语义 |
| --- | --- | --- |
| `title` | 非空 string | `h2` 或 `div.pod-title` 文本；缺少或为空时使用 `Wolfram Alpha 结果` |
| `href` | string，固定 `""` | 当前实现未为展示区域关联来源地址 |
| `body` | 非空 string | `div.result-content` 或 `div.pod-content` 文本，连接后 strip |
| `engine` | string，固定 `wolfram` | 本地标识 |

加入条目的条件只有 `body` 非空，标题允许通过固定默认值补充。`href` 始终为空字符串，不是 null，也没有隐含查询页面地址。文本节点直接连接，内部空白和段落边界没有统一处理；某一容器解析异常会被跳过。若 pod 主要以图片或动态组件展示且缺少文字节点，不会产生条目。

`body` 是知识或计算区域的文字，可包含数值、公式说明、定义或输入解释，无法视为目标文章全文。数值和单位均作为文本输出，没有结构化计算值。独立 pod 标识、公式格式、图片、来源引用、假设条件、交互控件和发布时间均未单独保留；出现的日期只属于计算文字。

联合入口 `wolfram_direct` 通过通用脚本适配保留 `title/href/body/engine`，当前没有进入 `NATIVE_WEB_SCRIPTS` 的标准化阶段，不生成 `url/content/published/thumbnail/sources`。若后续直接将这些非空条目交给通用 `normalize_item()`，固定空 href 无法通过绝对 HTTP(S) 校验；当前输出本身不支持依靠链接进行网页筛选或正文抓取。混合联合结果的字段应按实际聚合路径解释。

证据为该脚本、共享基类、网页工具及联合标准化代码。`.work/output-analysis/no-api.json` 的真实服装关键词查询执行成功但 `items:[]`、`total:0`，未观察到非空知识区域。表中字段和空链接行为仅由源码确认，不能据此判断 Wolfram 对该查询是否存在计算答案。
