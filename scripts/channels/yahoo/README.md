# Yahoo 搜索模块

通过 Yahoo Search 真实网页搜索，无需 API Key。`yahoo_search.py` 提供唯一实现；`YahooSearchNoAPI` 和 `search_yahoo` 复用同一客户端，保留原有导入入口。

## 使用方法

```bash
python scripts/channels/yahoo/yahoo_search.py "python documentation" --json --pretty
python scripts/channels/yahoo/yahoo_no_api.py "人工智能 新闻" --page 2 --timelimit w --safesearch strict --timeout 45 --json
python scripts/channels/yahoo/yahoo_search.py "search query" --proxy http://127.0.0.1:7890 --json
```

两个脚本支持相同的命令行参数。

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词 | 必需 |
| `-p, --page` | 页码，从首页跟随真实下一页链接 | 1 |
| `-m, --max-results` | 当前页结果数量上限，零表示不限 | 不限 |
| `-t, --timelimit` | d / w / m；年度过滤不支持 | 无 |
| `-s, --safesearch` | off / moderate / strict | moderate |
| `--timeout` | 整个查询的请求时间预算，必须大于零 | 20 |
| `--proxy` | 显式代理地址 | 无 |
| `--json` | 输出 JSON | False |
| `--pretty` | 缩进 JSON | False |

代理还可通过进程环境变量 `YAHOO_PROXY` 或 `NO_API_KEY_PROXY` 设置，显式参数优先。模块不读取 `.env`。

## 协议与结果

使用 `curl_cffi.Session(impersonate='chrome')`，同一会话自动接收服务端 Cookie 并跟随 HTTP 重定向，包括服务端发出的 `YBV`。请求不生成 `_ylt`、`_ylu`。第二页及后续页使用当前页面提供的真实分页链接，保持查询与时间过滤；没有下一页链接时直接失败。

时间限制通过 `btf=d/w/m` 传递。安全设置通过 `sB` Cookie 的 `vm=p/i/r` 分别表示 off、moderate、strict。年度过滤直接抛出 `ValueError`，CLI 不提供该选项。

通过 lxml 提取 `algo-sr` 网页结果的标题与摘要。使用 URL 标准库提取 Yahoo 跟踪地址路径中的 `RU=` 并解码一次，保留目标 URL 原有编码。

每项包含 `title`、`url`、`content`、`href`、`body`、`engine`，其中 `href=url`、`body=content`、`engine=yahoo`。JSON 顶层保留 `query`、`page`、`total_results` 和 `results`。

不支持的参数、HTTP 错误、验证码、缺失结果结构直接抛出异常。`max_results` 限制指定页，不自动跨页补足。

## 依赖与验证

依赖项目的 `curl_cffi` 与 `lxml`，执行 `python -m pip install -r requirements.txt` 安装。

已运行英文 `python documentation` 和中文 `人工智能 新闻` 的首页、第二页真实查询，中文查询包含最近一周与严格安全过滤。结果保存在已忽略的 `.work/native-web/yahoo-*.json`。安全过滤强度由 Yahoo 服务执行；查询结果本身不能量化过滤准确率。
