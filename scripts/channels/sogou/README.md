# 搜狗网页搜索

无需 API Key，解析普通及图文网页结果，优先从 `data-url` 获取目标地址，并提取摘要。验证码跳转明确报告失败。

```bash
python union_search_cli.py platform sogou_direct "Python documentation" --limit 5 --param page=2 --timeout 20
python scripts/channels/sogou/sogou_no_api.py "服装行业流行趋势" --page 1 --timelimit d --timeout 20 --json
```

支持 `--page`、`--timelimit d/w/m/y`、`--proxy`、`--timeout`、`--max-results`。数量默认或 `0` 表示不限制本次页面条数。远程服务可能针对时效查询或连续访问要求验证码；不自动重试或切换来源。

JSON 使用 `{"results": [...]}`，每条包含 `title`、`url`、`content`、`engine` 和兼容字段 `href`、`body`。未知页面结构直接报告错误。依赖在项目根目录 `requirements.txt` 中声明。
