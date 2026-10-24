# 网页请求状态

`web_search.py` 提供统一请求、HTML 文档解析和结果校验。`request_state.py` 使用 Python 标准库 `sqlite3`，将 host 请求状态持久化至项目根目录 `.work/web-search-state.sqlite`。

## 请求预约与截止时间

每个请求 host 默认至少间隔 2 秒。SQLite 的 `BEGIN IMMEDIATE` 事务原子读取和更新预约时间，因此多个 CLI 进程共享同一预约记录。等待发生在提交事务之后，不占用数据库写入事务；等待结束后再次检查冷却。

预约等待、数据库锁等待与网络请求使用同一个单调时钟截止时间。无法在剩余预算内完成预约时直接抛出 `TimeoutError`。单次 `time.sleep` 至多 59 秒。网络请求只获得等待之后的剩余预算。

预约记录在请求之前持久化；进程提前终止时已经预约的时间仍然保留。host 使用小写主机名，不按照查询参数、渠道名称、端口或代理划分。客户端自动重定向保留既有行为，预约针对传入请求地址的 host；自动重定向的中间 host 没有单独预约。

## 冷却记录

- HTTP 429：读取 `Retry-After`，支持整数秒数和 HTTP-date；缺失或无效时默认冷却 300 秒。已过去的日期按零秒处理。保存状态后由 HTTP 客户端抛出原 HTTP 异常。
- 明确验证码：默认冷却 900 秒。信号包括响应地址或 `Location` 的验证码路径、Yandex 验证响应头、验证码表单或 iframe、验证页面标题、Quark 验证脚本。
- 冷却期间：预约立即抛出 `SearchBlockedError` 的专用子类，错误包含 host、`remaining` 秒数和原因；不会等待冷却结束或发送网络请求。
- 重复冷却：保留较晚的冷却结束时间，较短冷却不会覆盖较长冷却。

`block(response)` 是已明确识别验证码时的记录边界，保存响应 host 的冷却后抛出 `SearchBlockedError`。`document(response)` 在调用渠道解析器之前检查已知 DOM 信号。公共 `SearchBlockedError` 保持原有构造和继承行为。

框架只在冷却状态转换为公开异常时捕获 `CooldownActiveError`；HTTP 错误在调用 `raise_for_status()` 之前写入冷却。错误继续向调用方传播，不会重试、返回空结果或切换来源。未来渠道新增的验证码信号应纳入统一响应或 DOM 检测，或者在明确识别的位置调用 `block(response)`。

记录服务端阻止信号时使用独立的 1 秒数据库写入预算，以便网络预算耗尽后仍保存冷却；这一步不再发送请求。SQLite 文件或事务失败会直接暴露异常。

## 本地检查

状态模块可直接操作真实 SQLite 文件，无需访问网络：

```python
import time
from scripts.channels.no_api.request_state import RequestState

state = RequestState()
state.reserve('example.com', time.monotonic() + 5)
```

使用 `RequestState(path=...)` 可在 `.work/` 下独立数据库中检查跨进程预约和冷却，避免影响实际搜索 host。网络验证需要调用真实渠道并检查结果和状态。
