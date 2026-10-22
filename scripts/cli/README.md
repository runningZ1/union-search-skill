# Unified CLI

统一 CLI 入口：

```bash
python union_search_cli.py <command> [options]
```

也可直接运行：

```bash
python scripts/cli/main.py <command> [options]
```

## Commands

- `search`: 多平台聚合搜索
- `platform`: 单平台搜索
- `image`: 多平台图片搜索/下载
- `download`: 使用 yt-dlp 下载视频/音频（支持从搜索结果文件导入）
- `list`: 列出平台、分组和图片平台
- `schema`: 输出机器可读的能力描述（命令、平台、限额、错误码）
- `errors`: 输出错误码与退出码注册表
- `doctor`: 环境变量和依赖检查

## Examples

```bash
python union_search_cli.py list --pretty
python union_search_cli.py doctor --env-file .env --pretty
python union_search_cli.py search "LLM" --platforms github duckduckgo --limit 3 --pretty
python union_search_cli.py platform tavily "AI news" --limit 5 --pretty
python union_search_cli.py google "AI news" --limit 5 --pretty
python union_search_cli.py bing "AI news" --limit 5 --pretty
python union_search_cli.py bsearch "AI news" --limit 5 --pretty
python union_search_cli.py search "AI agent" --platforms youtube bilibili --limit 3 -o ./out/search.json --pretty
python union_search_cli.py image "cat" --platforms pixabay --limit 5 --output-dir ./search_output/images --pretty
python union_search_cli.py download "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --max-height 1080 --output-dir ./downloads --pretty
python union_search_cli.py download "https://youtu.be/Zh9IscszDQg" --cookies-file C:/path/cookies.txt --restrict-filenames --continue-download --pretty
python union_search_cli.py download --from-file ./out/search.json --platforms youtube bilibili --select 1,2 --output-dir ./downloads --pretty
```

## 机器契约

stdout 只包含一个 JSON 信封，诊断信息走 stderr。

```json
{"schema_version": "1.0", "ok": true, "type": "result", "data": {}, "meta": {"request_id": "req_...", "duration_ms": 42}}
```

失败时 `ok` 为 `false`，`type` 为 `error`，并带 `error` 对象：`code`、`message`、`retryable`、`outcome`、`details`、`next_actions`。`success`、`command`、`query`、`errors` 字段保留。

退出码：`0` 成功，`1` 内部错误，`2` 参数错误，`3` 缺少依赖，`4` 平台暂不可用（可重试），`130` 被中断。

全局旗标 `--quiet` 关闭 stderr 诊断，`--no-color` 关闭人类可读输出的颜色，两者写在子命令前后都生效。

## Notes

- 默认输出为 `json`，可用 `--format markdown|text` 切换。
- `search`/`platform` 支持 `--fail-on-platform-error`，平台失败时返回退出码 `4`。
- `platform` 支持 `--param key=value` 透传参数给适配层。
- 单平台可直接使用平台名命令（例如 `google`, `bing`），等价于 `platform <name>`.
- `search` 返回中包含 `download_candidates`（稳定索引），可直接用于 `download --from-file --select`。
- `download` 依赖本机安装 `yt-dlp`；如需音视频合并/转音频，建议同时安装 `ffmpeg`。
- YouTube 403 时优先使用 `--cookies-file`；未显式传入时会尝试自动发现 `YTDLP_COOKIES_FILE` 或 `~/.claude/skills/yt-dlp-skill/cookies/cookies.txt`。
