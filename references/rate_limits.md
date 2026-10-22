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
python scripts/channels/github_search/github_search.py rate-limit
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
python scripts/channels/github_search/github_search.py rate-limit
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

## Firecrawl

### 计费方式
- 搜索：每 10 条结果 2 credits，向上取整
- 抓取正文：1 credit/页，PDF 与 JSON 额外计费
- 多个来源时，`limit` 对每个来源分别生效

### 并发
- 官方未公开固定 QPS，超出配额返回 429
- 正文抓取比纯搜索慢，建议单次 `--scrape` 结果数不超过 10 条

---

## DeepSeek 联网搜索

### 限速
- 账号级约 100 QPS
- 超出后返回 429
- 大型工具链调用产生的搜索请求自 2026-11-01 起按次计费

### 计费
- 5 元/1000 次成功请求

---

## 腾讯元宝搜索（腾讯云 WSA）

### 限制
- 结果数量仅支持 10/20/30/40/50
- 请求超限返回 `RequestLimitExceeded`
- 账号欠费返回 `ResourceUnavailable`

### 版本差异
- 极速版不支持 `Mode`、`Cnt`、`Industry`、`Deeplinks`
- 旗舰版额外返回 `authority_level`、`deeplinks`、`pics`

---

## TinyFish

### 限速
- 默认 5 次/分钟，具体额度取决于套餐
- 超限返回 HTTP 429，错误码 `RATE_LIMIT_EXCEEDED`
- 没有 `Retry-After` 头，退避从 15 秒起

### 超时
- 典型延迟 1-3 秒，建议客户端超时 10 秒

---

## AnySearch

### 限速
- 匿名访问可用，限额较低
- 配置 API Key 后限额提高，具体数值见控制台

### 计费
- 按调用次数计费，套餐见官网定价页

---

## 阿里云百炼联网搜索

### 计费
- 模型 token 与搜索次数分别计费
- `search_strategy` 为 `agent`、`agent_max` 时额外按次计费
- 搜索次数记录在 `usage.plugins.search.count`

### 模型限制
- `freshness`、`assigned_site_list`、`intention_options` 仅 `turbo` 策略支持
- qwen3.8 系列不支持 `agent` 策略

---

## 知乎开放平台

### 配额
- 站内搜索每次最多 10 条，全网搜索最多 20 条，热榜最多 30 条
- 具体调用额度由开放平台账号套餐决定

### 超时
- 官方 Skill 使用 5 秒超时，本项目默认 10 秒

---

## Cloudflare Web Search

### 限制
- 关键词最长 1024 字符
- 单次最多 10 条结果
- `byok_alias` 指向不存在的密钥时返回 HTTP 400

### 计费
- 按 AI Gateway 额度计费，价格与提供商标价相同
- ceramic 0.25 美元、linkup 5 美元、exa 7 美元，均为每 1000 次请求
- 使用自己的提供商密钥时由提供商计费

---

## Parallel Search

### 限速
- 默认 600 次/分钟，每次 `POST /v1/search` 计 1 次

### 模式
- `turbo` p50 约 200 毫秒，`fast` 约 700 毫秒，`advanced` 约 3 秒
- 参数错误返回 HTTP 422

---

## Querit 搜索

### 限速
- 官方未公布具体配额
- 超出速率限制返回 HTTP 429
- 密钥无效返回 HTTP 401

### 超时
- 官方 SDK 默认 60 秒，本项目默认 60 秒

---

## Ollama Web Search

### 限制
- 单次最多 10 条，默认 5 条
- 官方文档未公布速率限制与价格
- 单条摘要可能达到数千 token

---

## 智谱网络搜索

### 限制
- 关键词最长 70 个字符
- 结果数量 1-50；搜狗只接受 10、20、30、40、50
- 并发超限返回错误码 1701

### 计费
- `search_std` 0.01 元/次
- `search_pro` 0.03 元/次
- `search_pro_sogou`、`search_pro_quark` 各 0.05 元/次

---

## Kimi 搜索

### 限制
- 结果数量 1-20，默认 5
- 站点最多 5 个
- 服务端超时 1-60 秒

### 计费
- 基础搜索 0.01 元/次，专业搜索 0.015 元/次
- 页面抓取 0.01 元/次
- 费用与模型 token 分开计算

---

## 总结

| 平台 | 免费配额 | 速率限制 | 建议间隔 |
|------|----------|----------|----------|
| GitHub | 30 次/分钟 | 已认证 | 2 秒 |
| YouTube | 10,000 单位/天 | 配额制 | - |
| Google Search | 100 次/天 | 每日限制 | - |
| Tavily | 1,000 积分/月 | 积分制 | - |
| Firecrawl | 无免费额度说明 | credits 计费 | - |
| DeepSeek 搜索 | 无免费额度说明 | 100 QPS | - |
| 腾讯元宝搜索 | 按服务购买 | 接口限流 | - |
| TinyFish | 免费额度 | 5 次/分钟 | 12 秒 |
| AnySearch | 匿名可用 | 匿名限额较低 | - |
| 阿里云百炼 | 按量计费 | 模型限流 | - |
| 知乎开放平台 | 按账号套餐 | 接口限流 | - |
| Cloudflare Web Search | 按网关额度 | 单次 10 条 | - |
| Parallel Search | 按调用计费 | 600 次/分钟 | - |
| Querit | 按账号套餐 | 接口限流 | - |
| Ollama Web Search | 免费账号 | 未公布 | - |
| 智谱网络搜索 | 按次计费 | 并发受限 | - |
| Kimi 搜索 | 按次计费 | 单次 20 条 | - |
| Reddit | 无限制 | 反爬虫 | 2-3 秒 |
| DuckDuckGo | 无限制 | 隐性限制 | 1-2 秒 |
| Brave | 无限制 | 隐性限制 | 1-2 秒 |
| Yahoo | 无限制 | 隐性限制 | 1-2 秒 |
| Bing | 无限制 | 隐性限制 | 1-2 秒 |
| Wikipedia | 无限制 | 隐性限制 | 1 秒 |
| Anna's Archive | 无限制 | 隐性限制 | 2-3 秒 |
| 图片搜索 | 无限制 | 反爬虫 | 1-2 秒 |
