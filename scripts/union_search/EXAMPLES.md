# Union Search 使用示例

本文档提供 union_search 模块的实际使用示例。

## 基础示例

### 1. 列出所有可用平台

```bash
python union_search.py --list-platforms
```

### 2. 搜索所有平台（默认每个平台 3 条结果）

```bash
python union_search.py "machine learning"
```

### 3. 搜索指定平台

```bash
# 搜索 GitHub 和 Reddit
python union_search.py "Python" --platforms github reddit

# 搜索多个社交媒体平台
python union_search.py "美食" --platforms xiaohongshu douyin bilibili
```

### 4. 使用平台组

```bash
# 搜索开发者平台
python union_search.py "React" --group dev

# 搜索社交媒体
python union_search.py "旅游" --group social

# 搜索所有搜索引擎
python union_search.py "Python tutorial" --group search

# 搜索所有平台
python union_search.py "AI" --group all
```

## 高级示例

### 5. 自定义结果数量

```bash
# 每个平台返回 5 条结果
python union_search.py "深度学习" --limit 5

# 每个平台返回 1 条结果（快速预览）
python union_search.py "Vue.js" --limit 1
```

### 6. JSON 输出

```bash
# 紧凑 JSON 格式
python union_search.py "Django" --json

# 格式化 JSON（便于阅读）
python union_search.py "Flask" --json --pretty
```

### 7. 保存结果到文件

```bash
# 保存为 Markdown
python union_search.py "Rust" -o results.md

# 保存为 JSON
python union_search.py "Go" --json -o results.json

# 保存格式化 JSON
python union_search.py "Kotlin" --json --pretty -o results.json
```

### 8. 调整并发和超时

```bash
# 增加并发数（更快但消耗更多资源）
python union_search.py "AI" --max-workers 10

# 增加超时时间（网络慢时）
python union_search.py "ML" --timeout 120

# 组合使用
python union_search.py "DL" --max-workers 8 --timeout 90
```

## 实际应用场景

### 场景 1: 技术调研

快速了解某个技术在不同平台的讨论情况：

```bash
python union_search.py "Svelte" --group dev --limit 5 -o svelte_research.md
```

### 场景 2: 内容发现

在社交媒体上寻找热门内容：

```bash
python union_search.py "健身" --group social --limit 3 --json --pretty -o fitness_content.json
```

### 场景 3: 学习资源搜索

在搜索引擎中查找学习资源：

```bash
python union_search.py "Python tutorial for beginners" --group search --limit 5
```

### 场景 4: 跨平台对比

对比同一关键词在不同平台的结果：

```bash
python union_search.py "ChatGPT" --platforms github reddit twitter --limit 3 -o chatgpt_comparison.md
```

### 场景 5: 快速预览

快速浏览多个平台的最新内容：

```bash
python union_search.py "AI news" --group all --limit 1
```

## 输出示例

### Markdown 输出示例

```markdown
# 联合搜索结果: machine learning

**搜索时间**: 2024-01-15T10:30:00
**平台数量**: 2
**成功**: 2 | **失败**: 0
**总结果数**: 6

---

## GITHUB

✅ 找到 3 条结果

### 1. tensorflow/tensorflow
- **链接**: https://github.com/tensorflow/tensorflow
- **描述**: An Open Source Machine Learning Framework for Everyone
- **评分**: 175000

### 2. scikit-learn/scikit-learn
- **链接**: https://github.com/scikit-learn/scikit-learn
- **描述**: scikit-learn: machine learning in Python
- **评分**: 55000

---

## REDDIT

✅ 找到 3 条结果

### 1. Best resources for learning ML?
- **链接**: https://reddit.com/r/MachineLearning/...
- **作者**: user123
- **评分**: 1250

---
```

### JSON 输出示例

```json
{
  "keyword": "machine learning",
  "platforms": ["github", "reddit"],
  "limit_per_platform": 3,
  "timestamp": "2024-01-15T10:30:00",
  "results": {
    "github": {
      "platform": "github",
      "success": true,
      "items": [
        {
          "name": "tensorflow/tensorflow",
          "url": "https://github.com/tensorflow/tensorflow",
          "description": "An Open Source Machine Learning Framework for Everyone",
          "stars": 175000
        }
      ],
      "total": 3
    },
    "reddit": {
      "platform": "reddit",
      "success": true,
      "items": [
        {
          "title": "Best resources for learning ML?",
          "url": "https://reddit.com/r/MachineLearning/...",
          "author": "user123",
          "score": 1250
        }
      ],
      "total": 3
    }
  },
  "summary": {
    "total_platforms": 2,
    "successful": 2,
    "failed": 0,
    "total_items": 6
  }
}
```

## 常见问题

### Q: 如何只搜索特定几个平台？

使用 `--platforms` 参数：

```bash
python union_search.py "keyword" --platforms github reddit xiaohongshu
```

### Q: 如何加快搜索速度？

1. 减少平台数量
2. 减少每个平台的结果数量（`--limit 1`）
3. 增加并发数（`--max-workers 10`）

```bash
python union_search.py "keyword" --platforms github reddit --limit 1 --max-workers 5
```

### Q: 某个平台搜索失败怎么办？

单个平台失败不会影响其他平台。检查：
1. 该平台的搜索脚本是否存在
2. API 密钥是否配置正确
3. 网络连接是否正常

### Q: 如何查看详细错误信息？

查看输出中的错误信息，或使用 JSON 格式查看详细结果：

```bash
python union_search.py "keyword" --json --pretty
```

### Q: 可以自定义平台组吗？

目前平台组是预定义的。如需自定义，可以直接使用 `--platforms` 参数指定平台列表。

## 性能建议

1. **小规模测试**: 先用少量平台测试（`--platforms github reddit`）
2. **合理限制**: 每个平台 1-3 条结果通常足够（`--limit 3`）
3. **并发控制**: 根据网络情况调整并发数（`--max-workers 5`）
4. **超时设置**: 网络慢时增加超时（`--timeout 120`）

## 下一步

- 查看 [UNION_SEARCH_README.md](UNION_SEARCH_README.md) 了解详细文档
- 查看 [API 凭据获取指南](../../references/api_credentials.md) 配置 API
- 查看各平台的 README 了解平台特定功能
