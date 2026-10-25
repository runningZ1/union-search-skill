# DuckDuckGo 网页搜索

无需 API Key，使用 curl_cffi 请求首页提供的网页结果接口，通过 JSON 读取标题、URL 和摘要。`duckduckgo` 与兼容名称 `duckduckgo_html` 共用实现。联合请求同时指定两个名称时，仅执行一次。

```bash
python scripts/union_search_cli.py platform duckduckgo "Python packaging" --limit 5 --param page=1 --timeout 25
python scripts/channels/duckduckgo/duckduckgo_search.py "Python packaging" --page 2 --max-results 5 --timeout 25 --json --pretty
```

`--page` 默认为 1。后续页面按照服务返回的继续链接顺序获取，共享 `--timeout` 的截止时间。`--max-results` 默认不限制本次页面条数，`0` 同样表示不限制。

网页接口不提供本实现可验证的地区和时效筛选；传入非默认 `--region` 或 `--timelimit` 会明确失败。查询长度为 1 到 499 个字符。验证码、JavaScript 验证、缺少结果接口或无效响应直接报告错误。

`--proxy` 可指定代理；也可设置 `DUCKDUCKGO_PROXY` 或 `NO_API_KEY_PROXY`。统一 CLI 读取项目环境配置，独立脚本读取已经导出的环境变量。

结果提供 `title`、`url`、`content`、`engine`、`source_rank`，兼容字段 `href`、`body` 与对应字段内容一致。`duckduckgo_no_api.py` 保留旧函数和命令入口。

依赖通过项目根目录的 `requirements.txt` 安装。
