# Union Search

统一多平台搜索编排器。核心目标是：同一关键词并发调用多个平台，输出一份聚合 JSON，并显式标注每个平台成功或失败。

## 核心能力

- 并发调用多个平台，单平台失败不影响整体结果生成。
- 默认透传各平台原始结果结构，不做跨平台去重。
- 支持统一 JSON 输出到文件。
- 每个平台返回 `success/error/total/items/timing_ms`，便于排障。

## 快速开始

在 `scripts/union_search` 目录执行：

```bash
python union_search.py --list-platforms
python union_search.py "人工智能" --group dev --json --pretty
python union_search.py "人工智能" --platforms github reddit wikipedia -o result.json --json --pretty
```

## 常用参数

- `keyword`: 搜索关键词。
- `--platforms -p`: 指定平台列表。
- `--group -g`: 平台组（`dev/social/search/rss/all`）。
- `--limit -l`: 每个平台返回条数；不指定时使用平台自身默认行为。
- `--max-workers`: 并发数。
- `--timeout`: 总体等待超时（秒）。
- `--json --pretty`: 以格式化 JSON 输出。
- `--output -o`: 写入输出文件。
- `--verbose -v`: 打开详细日志。

## 输出结构

```json
{
  "keyword": "人工智能",
  "platforms": ["github", "wikipedia"],
  "timestamp": "2026-02-26T22:00:00",
  "results": {
    "github": {
      "success": true,
      "error": null,
      "total": 10,
      "timing_ms": 820,
      "items": []
    },
    "wikipedia": {
      "success": false,
      "error": "...",
      "total": 0,
      "timing_ms": 1040,
      "items": []
    }
  },
  "summary": {
    "total_platforms": 2,
    "successful": 1,
    "failed": 1,
    "total_items": 10
  }
}
```

## 使用建议

- 先用少量平台验证配置，再扩展到全平台。
- 对 API 平台先检查 `.env` 中对应密钥是否存在。
- 结果质量核对时，优先比对单平台独立调用与 union 聚合中的同平台条目。

## 相关文档

- 平台凭据说明：`references/api_credentials.md`
- 故障排查：`references/troubleshooting.md`
- 编排方案文档：`references/union_search_orchestrator_prd.md`
