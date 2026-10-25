# AI coding 工具原生搜索

三个实现已直接迁入本目录，不导入、不执行也不依赖 `D:\Projects\agent-search-extraction`。代码以该项目已有实现为基础，只调整本地包路径、统一入口适配、进程超时与原生工具调用验证。

## 使用

需要 Python 3.10+。先以当前系统用户安装并登录对应客户端，再在仓库根目录执行：

```bash
python scripts/union_search_cli.py doctor --platforms claude_code codex grok_build --pretty
python scripts/union_search_cli.py platform claude_code "SQLite WAL 官方文档" --limit 3 --timeout 180 --pretty --fail-on-platform-error
python scripts/union_search_cli.py platform codex "Python asyncio TaskGroup 官方文档" --limit 3 --timeout 180 --pretty --fail-on-platform-error
python scripts/union_search_cli.py platform grok_build "SQLite WAL 官方文档" --limit 3 --timeout 180 --pretty --fail-on-platform-error
python scripts/union_search_cli.py search "Python asyncio TaskGroup 官方文档" --group ai_tools --limit 2 --timeout 180 --pretty --fail-on-platform-error
```

`ai_tools` 是独立的本机账号分组，不进入默认 `general` 或 API Key 分组 `api`；显式 `all` 包含它们。联合调用会分别消耗三家账号额度。无需另填 API Key 不等于免费或无需会员，具体资格由客户端、账号套餐和额度决定。`doctor` 只检测本地认证线索，不验证远程额度。

| 渠道 | 原生实现 | 本地要求 |
| --- | --- | --- |
| `claude_code` | `claude -p`，只开放 WebSearch；事件流中必须有 WebSearch 调用 | Claude Code 已登录，默认模型 `haiku` |
| `codex` | 使用本机 Codex OAuth 登录态调用账号搜索端点 | 本机 Codex 登录；端点非公开稳定 API，可能变动 |
| `grok_build` | `grok -p`，只开放 web_search / web_fetch；事件流中必须有 web_search 调用 | Grok Build 已登录，默认模型 `grok-4.5` |

每次明确调用指定后端，没有 auto 路由，也不会降级到其他服务。搜索结果保留 `backend` 和 `untrusted: true`。默认不设置条数上限，`--limit 0` 也表示不限；正整数 `--limit N` 保留显式上限，原先最多 20 条的适配器限制已移除。实际数量仍受搜索端点、模型输出窗口、工具轮次与超时约束，不自动无限翻页。

## 可选参数

```bash
python scripts/union_search_cli.py platform codex "Python releases" --limit 3 --param recency_days=7 --param domains=python.org,docs.python.org --timeout 180 --pretty
```

`recency_days` 必须为正整数，`domains` 为逗号分隔域名。Claude/Grok 的时间、域名条件通过提示词传递，属于模型遵循的条件；Codex 传给原生搜索请求。其他透传参数会被拒绝。

可用环境变量：`CLAUDE_BIN`、`GROK_BIN` 指定原生程序；`CLAUDE_SEARCH_MODEL`、`GROK_MODEL` 选择模型；`CODEX_AUTH_FILE` 指定 Codex 登录文件。默认使用当前用户的凭据，不复制凭据到项目。Codex 遇到 401 时沿用迁入实现进行一次续期，回写前备份 auth 文件。

`UNIFIED_SEARCH_DEBUG_DIR` 可选保存原生响应，仅用于本地诊断，建议指向被忽略的 `search_logs/`。响应可能含查询和会话标识，不应提交。对外错误不回传原生 stdout、stderr 或认证响应正文。

## 实现与内部验证

- `native_search/` 保存迁入的三家后端与辅助代码，不使用源项目的自动降级路由。
- `adapter.py` / `worker.py` 通过 JSON stdin/stdout 调用，输入不进入 shell。
- 每次查询使用临时工作目录；超时终止 worker 及其子进程树，避免子 CLI 继续运行。
- Windows 的 Claude npm CMD shim 解析到原生 exe 后调用，保留中文、换行和 JSON 引号。
- Claude / Grok 的事件流必须出现对应工具调用，随后才解析最终结构化结果。
- 代码回归测试保存在 `scripts/tests/`，执行方式与现有用例限制见[测试目录说明](../../tests/README.md)；在线三端验收必须单独运行。

集成验收记录保存在本机 `search_logs/ai-tools-integration/`。当前只把关键词搜索接入统一入口；迁入代码保留的 fetch / research 方法未新增公开 CLI 命令。
