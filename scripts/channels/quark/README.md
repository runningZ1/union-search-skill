# Quark 网页搜索

`quark_no_api.py` 使用 `curl_cffi` 请求 Quark 搜索页面，以 `lxml` 定位 hydration JSON，再用标准库 `json` 读取结果数据，无需 API Key。

```bash
python scripts/channels/quark/quark_no_api.py "Python documentation" -m 5 --json
python scripts/channels/quark/quark_no_api.py "北京大学" --page 2 --timeout 20 --json
python scripts/channels/quark/quark_no_api.py "Python documentation" --proxy http://127.0.0.1:7890 --json
```

Python 入口：

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("scripts/channels").resolve()))
from quark.quark_no_api import search_quark

results = search_quark("Python documentation", max_results=5, proxy=None, page=1, timeout=20)
```

`max_results=None` 或 `max_results=0` 返回请求页面的全部受支持结果。`page` 从一开始，仅请求指定页面。`timeout` 单位为秒。显式代理通过 `proxy` 或 `--proxy` 传入。

每条结果包含 `title`、`url`、`content`、`engine="quark"`，以及兼容字段 `href`、`body`。`category` 保留服务返回的卡片类别。`--json` 输出 `{"results": [...]}` JSON 对象；默认输出标题、地址和摘要。

端点为 `https://quark.sm.cn/s`，参数为 `q`、`layout=html` 和 `page`。结果来自 `type="application/json"`、`id="s-data-*"`、`data-used-by="hydrate"` 的脚本元素；卡片类别为 `extraData.sc`，卡片内容为 `data.initialData`。

支持 `ss_doc`、`ss_kv`、`ss_pic`、`ss_text`、`ss_video`、`baike`、`structure_web_novel` 文档卡片，以及 `nature_result`、`addition`、`ss_note`、`baike_sc`、`news_uchq`、`ai_page` 网页卡片。其他卡片类型不提供网页结果。标题和摘要中的 HTML 使用 `lxml` 转为文本。端点与字段事实参考本地 SearXNG 引擎资料，模块独立实现，未引入其代码。

HTTP 错误、验证码、缺少 hydration 结构、没有受支持的网页卡片、无效 JSON 或结果字段会直接抛出异常。不会自动重试 HTTP 429。

依赖 `curl_cffi`、`lxml` 和共享模块 `scripts/channels/no_api/web_search.py`。此模块不读取 `.env`。
