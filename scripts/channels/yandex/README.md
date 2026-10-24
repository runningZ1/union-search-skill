# Yandex 搜索

## 网页搜索

`yandex_no_api.py` 使用 `curl_cffi` 请求 Yandex 站点搜索页面，以 `lxml` 解析标题、地址和摘要，无需 API Key。

```bash
python scripts/channels/yandex/yandex_no_api.py "Python documentation" -m 5 --json
python scripts/channels/yandex/yandex_no_api.py "北京大学" --page 2 --timeout 20 --json
python scripts/channels/yandex/yandex_no_api.py "Python documentation" --proxy http://127.0.0.1:7890 --json
```

Python 入口：

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("scripts/channels").resolve()))
from yandex.yandex_no_api import search_yandex

results = search_yandex("Python documentation", max_results=5, proxy=None, page=1, timeout=20)
```

`max_results=None` 或 `max_results=0` 返回请求页面的全部结果。`page` 从一开始，仅请求指定页面，发送给 Yandex 的 `p` 为 `page - 1`。`timeout` 单位为秒。显式代理通过 `proxy` 或 `--proxy` 传入。

每条结果包含 `title`、`url`、`content`、`engine="yandex"`，以及兼容字段 `href`、`body`。`--json` 输出 `{"results": [...]}` JSON 对象；默认输出标题、地址和摘要。

请求端点为 `https://yandex.com/search/site/`，参数包括 `text`、`tmpl_version=releases`、`web=1`、`frame=1`、`searchid=3131712`。HTML 结果来自 `b-serp-item`，标题链接来自 `b-serp-item__title-link`，摘要来自 `b-serp-item__text`。端点与字段事实参考本地 SearXNG 引擎资料，模块独立实现，未引入其代码。

HTTP 错误、验证码、无结果结构、无效标题或地址会直接抛出异常。不会自动重试 HTTP 429。没有可识别的结果时不将页面判定为成功空结果。

依赖 `curl_cffi`、`lxml` 和共享模块 `scripts/channels/no_api/web_search.py`。此模块不读取 `.env`。

## SerpAPI 搜索

现有 `yandex_search.py` 提供 SerpAPI 渠道，调用方式见该脚本的 `--help`。
