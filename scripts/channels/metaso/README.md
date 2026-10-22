# 秘塔搜索 (Metaso Search)

## 概述

秘塔搜索是一个 AI 驱动的网络搜索引擎，提供高质量搜索结果和智能摘要。

## 特性

- ✅ AI 生成的搜索结果摘要
- ✅ 高质量搜索结果
- ✅ 支持网页和文件搜索
- ✅ 简洁的片段展示
- ✅ 积分管理系统

## 环境配置

### 方式一：环境变量

```bash
# Linux/macOS
export METASO_API_KEY="your_api_key_here"

# Windows PowerShell
$env:METASO_API_KEY="your_api_key_here"
```

### 方式二：.env 文件

在项目根目录创建 `.env` 文件：

```
METASO_API_KEY=your_api_key_here
```

## 使用示例

### 基本搜索

```bash
python metaso_search.py "搜索关键词"
```

### 指定结果数量

```bash
python metaso_search.py "Python 教程" --size 20
```

### JSON 输出

```bash
python metaso_search.py "机器学习" --format json
```

### 简要列表格式

```bash
python metaso_search.py "AI 发展" --format brief
```

### 不包含 AI 摘要

```bash
python metaso_search.py "技术文档" --no-summary
```

### 搜索文件

```bash
python metaso_search.py "论文 PDF" --scope file
```

## 在代码中使用

```python
from metaso_search import MetasoClient, format_markdown

# 创建客户端
client = MetasoClient()

# 执行搜索
result = client.search(
    query="如何学习 Python",
    size=10,
    include_summary=True
)

# 格式化输出
print(format_markdown(result))
```

## 参数说明

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `query` | string | 必需 | 搜索关键词 |
| `size` | int | 10 | 返回结果数量 (1-50) |
| `scope` | str | "webpage" | 搜索范围: webpage 或 file |
| `include_summary` | bool | True | 是否包含 AI 摘要 |
| `include_raw_content` | bool | False | 是否包含原始内容 |
| `concise_snippet` | bool | True | 使用简洁片段 |

## 输出格式

### Markdown 格式（默认）

```markdown
# 搜索结果: 关键词

**找到 160 条结果，显示前 10 条** | 剩余积分: 99

---

## 1. 标题
**链接**: https://example.com
**日期**: 2024-01-15
**相关度**: high

**摘要**:
AI 生成的摘要内容...
```

### JSON 格式

```json
{
  "query": "关键词",
  "total": 160,
  "credits": 99,
  "webpages": [
    {
      "position": 1,
      "title": "标题",
      "link": "https://example.com",
      "score": "high",
      "date": "2024-01-15",
      "summary": "摘要..."
    }
  ]
}
```

## 最佳实践

1. **合理设置 size**: 一般搜索用 10-15，深度研究用 20-30
2. **使用摘要功能**: AI 摘要可快速了解内容，减少阅读时间
3. **错误处理**: 遇到 429 错误时等待几秒后重试
4. **积分管理**: 关注 `credits` 字段，合理规划 API 使用

## 故障排除

### API Key 未设置

```
错误: API 密钥未设置。请通过以下方式之一提供:
1. 传入 api_key 参数
2. 设置环境变量 METASO_API_KEY
3. 创建 .env 文件并添加 METASO_API_KEY=your_key
```

### 积分不足

```
搜索失败: API 请求失败: 429 - {"error": "Insufficient credits"}
```

解决：检查账户积分余额，或等待配额重置。

## 获取 API Key

访问秘塔搜索官网获取 API Key：https://metaso.cn
