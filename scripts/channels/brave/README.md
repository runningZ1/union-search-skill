# Brave 搜索模块

通过 Brave Search 真实网页搜索，无需 API Key。`brave_search.py` 提供唯一实现；`BraveSearchNoAPI` 和 `search_brave` 复用同一客户端，保留原有导入入口。

## 使用方法

```bash
python scripts/channels/brave/brave_search.py "python documentation" --json --pretty
python scripts/channels/brave/brave_no_api.py "人工智能 新闻" --page 2 --timelimit w --safesearch strict --timeout 30 --json
python scripts/channels/brave/brave_search.py "local news" --country us --proxy http://127.0.0.1:7890 --json
```

两个脚本支持相同的命令行参数。

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词 | 必需 |
| `-p, --page` | 页码，范围 1–10 | 1 |
| `-m, --max-results` | 当前页结果数量上限，零表示不限 | 不限 |
| `-c, --country` | 两个字母的国家代码或 `all` | us |
| `-s, --safesearch` | off / moderate / strict | moderate |
| `-t, --timelimit` | d / w / m / y | 无 |
| `--timeout` | 请求超时秒数，必须大于零 | 20 |
| `--proxy` | 显式代理地址 | 无 |
| `--json` | 输出 JSON | False |
| `--pretty` | 缩进 JSON | False |

代理还可通过进程环境变量 `BRAVE_PROXY` 或 `NO_API_KEY_PROXY` 设置，显式参数优先。模块不读取 `.env`。

## 协议与结果

使用 `curl_cffi.Session(impersonate='chrome')` 请求 Brave。分页使用 `offset=page-1`，时间限制映射为 `tf=pd/pw/pm/py`。地区与安全搜索通过 `country`、`safesearch` Cookie 传递，设置 `useLocation=0`、`summarizer=0`。

通过 lxml 读取实际 HTML 中 `data-type="web"` 的结果及其标题链接与摘要，只返回网页结果。每项包含 `title`、`url`、`content`、`href`、`body`、`engine`，其中 `href=url`、`body=content`、`engine=brave`。JSON 顶层保留 `query`、`page`、`country`、`total_results` 和 `results`。

不支持的参数、HTTP 错误、验证码、缺失结果结构直接抛出异常。`max_results` 限制当前页，不自动跨页补足。

## 依赖与验证

依赖项目的 `curl_cffi` 与 `lxml`，执行 `python -m pip install -r requirements.txt` 安装。

已运行英文 `python documentation` 和中文 `人工智能 新闻` 的首页、第二页真实查询，中文查询包含最近一周与严格安全过滤。结果保存在已忽略的 `.work/native-web/brave-*.json`。安全过滤强度由 Brave 服务执行；查询结果本身不能量化过滤准确率。
