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
- `list`: 列出平台、分组和图片平台
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
python union_search_cli.py image "cat" --platforms pixabay --limit 5 --output-dir ./search_output/images --pretty
```

## Notes

- 默认输出为 `json`，可用 `--format markdown|text` 切换。
- `search`/`platform` 支持 `--fail-on-platform-error`，在平台失败时返回非零退出码。
- `platform` 支持 `--param key=value` 透传参数给适配层。
- 单平台可直接使用平台名命令（例如 `google`, `bing`），等价于 `platform <name>`.
