# 百度搜索

`baidu_no_api.py` 使用百度搜索页面的 DOM 获取网页结果，无需 API Key。请求通过共享 `no_api.web_search` 的 session、request、document 接口执行，使用共享节流；模块不读取 `.env`。

```bash
python scripts/channels/baidu/baidu_no_api.py "光伏行业 市场报告" --max-results 8 --timeout 20 --json
```

保留 `BaiduSearchNoApi`、`search_baidu`、文本输出与 `{"results": [...]}` JSON 输出。`search_baidu` 和 CLI 均支持 `timeout`，单位为秒。

解析会过滤明确广告标记、百度 `/baidu.php` 广告链接以及百度图片、视频搜索聚合入口。标题链接优先采用 `data-tools` JSON 中的目标地址，并读取普通结果容器的 `mu` 目标地址。模块不会逐个请求跳转链接；无法获得目标地址时保留百度跳转链接，并设置 `link_type="redirect"`，获得目标地址时设置 `link_type="direct"`。

每条结果包含 `title`、`url`、`content`、`href`、`body`、`engine`、`link_type`。摘要读取页面摘要区域，缺失时保持空字符串。结果保持页面顺序，统一去重由编排层负责。HTTP 错误、验证码、无效 JSON 与无法识别的页面直接抛出异常，不重试、不切换搜索渠道。

2026-10-24 使用中文“光伏行业 2026 市场报告”和英文“healthcare industry market research 2026”各请求一次，均返回 HTTP 200。原始 HTML 位于已忽略的 `.work/industry-search-20261024/baidu_checks/html/`，解析分别得到 8 条与 9 条结果，均有摘要与直接地址。本次页面未出现广告和图片、视频聚合入口，未对这些分支作真实样本验证。
