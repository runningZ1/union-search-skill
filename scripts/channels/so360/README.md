# 360 网页搜索

无需 API Key，使用同一 HTTP 会话获取 Cookie 并查询结果。提取网页标题、目标链接和摘要，优先使用结果中的 `data-mdurl`。

```bash
python union_search_cli.py platform so360_direct "Python documentation" --limit 5 --param page=2 --timeout 20
python scripts/channels/so360/so360_no_api.py "服装行业流行趋势" --page 1 --timelimit m --timeout 20 --json
```

支持 `--page`、`--timelimit d/w/m/y`、`--proxy`、`--timeout`、`--max-results`。数量默认或 `0` 表示不限制本次页面条数；多个请求共享搜索截止时间。部分特殊卡片没有静态摘要，其 `content` 保持空值。验证码与未知页面结构直接报告失败。

JSON 使用 `{"results": [...]}`，每条包含 `title`、`url`、`content`、`engine` 和兼容字段 `href`、`body`。依赖在项目根目录 `requirements.txt` 中声明。
