# API 速率限制汇总

本文档汇总所有平台的 API 速率限制和配额信息。

## GitHub API

### 搜索 API
- **已认证**: 30 次搜索/分钟
- **未认证**: 10 次搜索/分钟

### 核心 API
- **已认证**: 5,000 次请求/小时
- **未认证**: 60 次请求/小时

### 检查速率限制
```bash
python scripts/github/github_search.py rate-limit
```

### 最佳实践
- 使用 token 认证提高限制
- 实现指数退避重试
- 缓存搜索结果
- 使用条件请求（ETag）

---

## YouTube Data API

### 配额系统
- **每日配额**: 10,000 单位（默认）
- **搜索请求**: 100 单位/次
- **Videos.list**: 1 单位/次
- **CommentThreads.list**: 1 单位/次

### 配额计算示例
```
搜索 10 个视频 = 100 单位
获取 10 个视频详情 = 10 单位
获取 10 个视频的评论 = 10 单位
总计 = 120 单位
```

### 配额用尽后
- 等待到第二天（太平洋时间午夜重置）
- 或申请增加配额

### 最佳实践
- 限制搜索结果数量
- 使用 `--max-results` 参数控制
- 避免频繁搜索相同内容
- 考虑缓存结果

---

## Google Custom Search API

### 免费套餐
- **每日配额**: 100 次查询
- **单次查询**: 最多 10 个结果

### 付费套餐
- **价格**: $5/1000 次查询
- **每日上限**: 10,000 次查询

### 最佳实践
- 使用精确的搜索关键词
- 利用高级搜索运算符（参考 `google_search_guide.md`）
- 避免重复查询
- 考虑使用无需 API 的替代方案（DuckDuckGo、Brave 等）

---

## Tavily Search API

### 免费额度
- **每月配额**: 1,000 积分
- **基础搜索**: 1 积分/次
- **高级搜索**: 2 积分/次

### 搜索深度消耗
- `basic`: 1 积分
- `advanced`: 2 积分
- `fast`: 1 积分

### 最佳实践
- 优先使用 `basic` 或 `fast` 模式
- 仅在需要时使用 `advanced` 模式
- 限制 `--max-results` 数量
- 避免包含 AI 答案（`--include-answer`）以节省积分

---

## TikHub API

### 配额系统
- 基于积分制
- 不同平台消耗不同积分
- 提供免费试用额度

### 支持平台
- 小红书（Xiaohongshu）
- 抖音（Douyin）
- Bilibili
- Twitter

### 最佳实践
- 查看 TikHub 官方文档了解最新定价
- 监控积分使用情况
- 合理设置 `--limit` 参数
- 避免过度请求

---

## 微博 API（Cookie 方式）

### 限制说明
- 无官方 API 速率限制文档
- 基于 Cookie 的爬虫方式
- 建议控制请求频率

### 最佳实践
- 请求间隔至少 1-2 秒
- 避免短时间大量请求
- 使用 `--limit` 控制结果数量
- Cookie 过期（约 3 个月）后及时更新

### 注意事项
- 过于频繁的请求可能导致账号被限制
- 无法爬取自己的微博
- 建议使用小号进行测试

---

## Reddit（无需 API）

### 限制说明
- 无需 API Key
- 基于网页爬虫
- 有反爬虫机制

### 最佳实践
- 使用 `--proxy` 参数避免 IP 封禁
- 请求间隔建议 2-3 秒
- 避免短时间大量请求
- 遇到 403 错误时使用代理

### 自动保护机制
- 内置自动重试
- 指数退避策略
- 限流保护

---

## 无需 API 密钥的平台

以下平台无需 API 密钥，但仍有隐性限制：

### DuckDuckGo
- 无官方速率限制
- 建议请求间隔 1-2 秒
- 过于频繁可能触发验证码

### Brave Search
- 无官方速率限制
- 建议请求间隔 1-2 秒
- 使用代理避免 IP 限制

### Yahoo Search
- 无官方速率限制
- 建议请求间隔 1-2 秒
- 自动处理 URL 重定向

### Bing Search
- 无官方速率限制
- 建议请求间隔 1-2 秒
- 支持多语言和地区

### Wikipedia
- 无官方速率限制
- 建议请求间隔 1 秒
- 遵守 robots.txt 规则

### Anna's Archive
- 无官方速率限制
- 建议请求间隔 2-3 秒
- 避免过度请求

---

## 图片搜索（17 个平台）

### 限制说明
- 完全独立，无需 API 密钥
- 基于 `pyimagedl` 库
- 各平台有不同的反爬虫机制

### 最佳实践
- 使用 `--threads` 控制并发数（默认 5）
- 使用 `--delay` 设置请求间隔（默认 1.0 秒）
- 避免单次下载过多图片
- 分批次下载大量图片

### 配置示例
```bash
# 保守配置（避免被封）
python scripts/union_image_search/multi_platform_image_search.py \
  --keyword "cats" \
  --num 50 \
  --threads 3 \
  --delay 2.0

# 激进配置（速度优先）
python scripts/union_image_search/multi_platform_image_search.py \
  --keyword "cats" \
  --num 100 \
  --threads 10 \
  --delay 0.5
```

---

## 通用最佳实践

### 1. 实现重试机制
```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
        return wrapper
    return decorator
```

### 2. 监控配额使用
- 定期检查 API 配额
- 记录每次请求的消耗
- 设置告警阈值

### 3. 缓存结果
- 缓存搜索结果避免重复请求
- 使用 `responses/` 目录保存原始响应
- 实现本地缓存机制

### 4. 错误处理
- 捕获速率限制错误（429）
- 实现指数退避重试
- 记录错误日志

### 5. 合理使用参数
- 使用 `--limit` 控制结果数量
- 避免请求过多数据
- 分批次处理大量请求

---

## 速率限制错误处理

### HTTP 状态码
- **429 Too Many Requests**: 超出速率限制
- **403 Forbidden**: 可能被封禁或需要认证
- **503 Service Unavailable**: 服务暂时不可用

### 处理策略
1. **429 错误**: 等待后重试（查看 `Retry-After` 头）
2. **403 错误**: 检查认证信息或使用代理
3. **503 错误**: 等待服务恢复

### 示例代码
```python
import requests
import time

def handle_rate_limit(response):
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"Rate limited. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        return True
    return False
```

---

## 配额监控工具

### GitHub
```bash
# 检查剩余配额
python scripts/github/github_search.py rate-limit
```

### YouTube
```bash
# 手动计算配额消耗
# 搜索: 100 单位 × 请求次数
# 详情: 1 单位 × 视频数量
```

### 其他平台
- 查看平台控制台
- 使用官方 API 监控工具
- 实现自定义监控脚本

---

## 总结

| 平台 | 免费配额 | 速率限制 | 建议间隔 |
|------|----------|----------|----------|
| GitHub | 30 次/分钟 | 已认证 | 2 秒 |
| YouTube | 10,000 单位/天 | 配额制 | - |
| Google Search | 100 次/天 | 每日限制 | - |
| Tavily | 1,000 积分/月 | 积分制 | - |
| TikHub | 试用额度 | 积分制 | - |
| 微博 | 无限制 | Cookie | 1-2 秒 |
| Reddit | 无限制 | 反爬虫 | 2-3 秒 |
| DuckDuckGo | 无限制 | 隐性限制 | 1-2 秒 |
| Brave | 无限制 | 隐性限制 | 1-2 秒 |
| Yahoo | 无限制 | 隐性限制 | 1-2 秒 |
| Bing | 无限制 | 隐性限制 | 1-2 秒 |
| Wikipedia | 无限制 | 隐性限制 | 1 秒 |
| Anna's Archive | 无限制 | 隐性限制 | 2-3 秒 |
| 图片搜索 | 无限制 | 反爬虫 | 1-2 秒 |
