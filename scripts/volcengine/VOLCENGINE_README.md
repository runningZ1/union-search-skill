# 火山引擎融合信息搜索 (Volcengine Search)

## 概述

火山引擎（字节跳动）融合信息搜索 API，提供 Web 搜索和 AI 摘要功能。

## 特性

- ✅ Web 搜索（标准版和 AI 摘要版）
- ✅ 丰富的卡片数据（天气、股票、汇率等）
- ✅ 权威度筛选
- ✅ 时间范围过滤
- ✅ 站点白名单/黑名单
- ✅ Query 改写优化
- ✅ 行业定制（金融、游戏）

## 环境配置

### 方式一：环境变量

```bash
# Linux/macOS
export VOLCENGINE_API_KEY="your_api_key_here"

# Windows PowerShell
$env:VOLCENGINE_API_KEY="your_api_key_here"
```

### 方式二：.env 文件

在项目根目录创建 `.env` 文件：

```
VOLCENGINE_API_KEY=your_api_key_here
```

## 使用示例

### Web 搜索

```bash
python volcengine_search.py web "北京旅游攻略"
```

### Web 搜索 + AI 摘要

```bash
python volcengine_search.py summary "人工智能发展趋势"
```

### Web 搜索 + AI 摘要

```python
from volcengine_search import VolcengineSearchClient

# 创建客户端
client = VolcengineSearchClient(api_key="your_api_key")

# Web 搜索
result = client.web_search(
    query="Python 教程",
    count=10,
    need_summary=True
)

# Web 搜索 + AI 摘要
result = client.web_search_summary(
    query="机器学习",
    count=10
)
```

# Web 搜索 + AI 摘要

### 1. Web 搜索

标准 Web 搜索，支持高级筛选：

```python
result = client.web_search(
    query="搜索关键词",
    count=10,                    # 返回结果数量（最多50）
    need_content=False,          # 是否需要正文内容
    need_url=True,               # 是否需要原文链接
    need_summary=True,           # 是否需要精准摘要
    time_range="OneWeek",        # 时间范围
    sites=["github.com"],        # 指定站点
    block_hosts=["spam.com"],    # 屏蔽站点
    auth_info_level=1,           # 权威度级别（0:不限制, 1:非常权威）
    query_rewrite=True,          # Query 改写
    industry="finance"           # 行业类型
)
```

### 2. Web 搜索总结版

包含大模型生成的 AI 摘要：

```python
result = client.web_search_summary(
    query="量子计算",
    count=10
)

# 获取 AI 摘要
summary = result["Choices"][0]["Message"]["Content"]
```

## 时间范围选项

- `OneDay` - 最近一天
- `OneWeek` - 最近一周
- `OneMonth` - 最近一个月
- `OneYear` - 最近一年
- `YYYY-MM-DD..YYYY-MM-DD` - 自定义日期范围

## 丰富卡片数据（火山如意）

搜索结果可能包含结构化卡片数据：

- 天气预报和空气质量
- 股票价格和金融数据
- 汇率和贵金属价格
- 节假日日历
- 火车/航班时刻表
- 演唱会信息
- 更多...

访问卡片数据：

```python
result = client.web_search(query="北京天气")
cards = result.get("Data", {}).get("CardResults", [])
for card in cards:
    card_type = card.get("CardType")
    card_data = card.get("CardData")
    # 处理卡片数据
```

## 速率限制

- 默认限制：5 QPS（每秒查询数）
- 可通过工单申请提升配额

## 免费额度

- Web 搜索：5,000 次免费调用
- Web 搜索总结版：5,000 次免费调用

## 错误处理

### 403 Access Denied

```python
# 检查 API Key 是否有效
# 子账号需要在 IAM 控制台授予 TorchlightApiFullAccess 权限
```

### 429 Rate Limit

```python
# 超过 5 QPS 限制，实现重试逻辑
import time
time.sleep(0.2)  # 等待 200ms 后重试
```

## 最佳实践

1. **API Key 安全**: 使用环境变量，不要硬编码
2. **速率控制**: 默认 5 QPS，实现指数退避重试
3. **Query 优化**:
   - 保持查询简洁（1-100 字符）
   - 复杂查询启用 `query_rewrite`
   - 使用行业定制搜索
4. **结果筛选**:
   - 使用 `auth_info_level=1` 获取权威来源
   - 应用时间范围获取最新内容
   - 使用 `block_hosts` 屏蔽低质量域名
5. **内容获取**:
   - 仅在需要时设置 `need_content=True`（增加响应大小）
   - 使用 `need_summary=True` 获取 300-500 字摘要
   - 默认包含约 100 字的片段

## 获取 API Key

1. 访问火山引擎控制台：https://console.volcengine.com/ask-echo/api-key
2. 导航到"融合信息搜索"部分
3. 创建新的 API Key
4. 安全存储密钥

## 限制

- Query 长度：1-100 字符（超长会被截断）
- 结果限制：
  - Web 搜索：最多 50 条/请求
- 速率限制：默认 5 QPS
- 域名过滤：`sites` 或 `block_hosts` 最多 5 个域名

## 故障排除

### 错误 100013 (AccessDenied)

- 确保 API Key 有效且激活
- 子账号需在 IAM 控制台授予 `TorchlightApiFullAccess` 权限
- 主账号访问无限制

### 空结果

- 尝试启用 `query_rewrite=True`
- 放宽时间范围或移除域名过滤
- 检查查询是否过于具体或包含拼写错误

### 响应慢

- 不需要时禁用 `query_rewrite`（增加延迟）
- 减少 `count` 参数
- 使用标准搜索而非摘要模式
