# Union Search

多渠道关键词搜索编排器。推荐从仓库根目录使用统一 CLI，默认只选择无需必填 API Key 的渠道。

## 快速开始

```bash
python union_search_cli.py list --type groups --pretty
python union_search_cli.py search "人工智能" --group general --limit 3 --pretty
python union_search_cli.py search "人工智能" --group api --limit 3 --pretty
python union_search_cli.py search "人工智能" --platforms github wikipedia --limit 3 --deduplicate --pretty
```

`api` 会请求该组的全部服务，需事先配置对应凭据。只想调用部分服务时，使用 `--platforms`。

## 分组

| 分组 | 范围 | 凭据要求 |
| --- | --- | --- |
| `general` | 25 个搜索渠道，默认分组 | 无需必填 API Key |
| `api` | 24 个搜索渠道 | 需要 API Key |
| `ai_tools` | Claude Code、Codex、Grok Build | 本机客户端登录与账号额度，不进入默认分组 |
| `search` / `no_api_key` | `general` 的兼容别名 | 无需必填 API Key；旧 `search` 不再混用 API 渠道 |
| `dev` | GitHub、Reddit | 无需必填 API Key，GitHub Token 可选 |
| `social` | YouTube、知乎开放平台、小宇宙 FM | 分别需要 YouTube、知乎开放平台、秘塔凭据 |
| `preferred` | 保留的 6 个无 Key 渠道预设 | 不代表实时健康状态 |
| `all` | 全部 52 个搜索渠道 | 包含需 API 和本机账号的渠道，不含正文提取工具 |
| `tools` | Defuddle | Node.js 依赖；使用 `defuddle <url>` 专用入口 |

“无需 API”指无需配置必填 API Key；部分渠道仍调用匿名远程接口。不同访问方式计为独立条目。分组和 CLI 凭据检查共用 [platform_metadata.py](platform_metadata.py)，新增渠道时须同步核对认证要求。

TikHub 搜索接入与相关六个入口已移除。独立的 `zhihu_official` 不受影响。RSS、微信等独立模块不属于本编排器的分组。

## 参数与行为

- `--platforms` 优先于 `--group`；两者都不指定时使用 `general`。
- 默认不做本地条数截断；`--limit 0` 同样表示不限。正整数 `--limit` 是每渠道上限；`--preset small/medium/large/extra` 对应 3/5/10/20 条。
- 不限条数仅针对已取得的结果，上游请求批量、分页容量、模型输出窗口及超时保持有效，不自动无限翻页。
- `--deduplicate` 按标题或链接进行跨渠道去重。
- `--max-workers` 控制并发，`--timeout` 设置超时秒数。
- 默认输出 JSON；`--pretty` 调整缩进，`--format markdown|text` 切换格式，`-o` 保存文件。
- 平台失败时检查顶层 `ok`；添加 `--fail-on-platform-error` 可让平台失败返回退出码 `4`。
- 渠道失败不会自动选择其他服务。无结果可能源于关键词、网络、限流或解析器问题。

## 旧模块入口

需要直接调用底层编排器时，从仓库根目录运行：

```bash
python -m scripts.union_search.union_search --list-platforms
python -m scripts.union_search.union_search "人工智能" --group general --json --pretty
```

旧模块与统一 CLI 使用相同分组和默认范围，但输出格式不同。旧模块支持 `--json`，统一 CLI 默认 JSON，不接受 `--json`。

## 验证与文档

```bash
python -m unittest discover -s tests -v
```

这些回归测试验证分组边界、默认路由、兼容别名及移除渠道的拒绝行为，不请求外部服务。

详见 [项目 README](../../README.md)、[统一 CLI](../cli/README.md) 和[凭据指南](../../references/api_credentials.md)。
