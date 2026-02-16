# Union Search 快速开始

## 一分钟上手

```bash
# 1. 列出所有可用平台
python union_search.py --list-platforms

# 2. 搜索开发者平台（GitHub + Reddit）
python union_search.py "Python" --group dev

# 3. 搜索所有平台
python union_search.py "AI" --group all --limit 2
```

## 核心功能

- ✅ 支持 17+ 个平台
- ✅ 并发搜索，速度快
- ✅ 统一接口，易使用
- ✅ 多种输出格式（Markdown/JSON）
- ✅ 灵活配置（平台、数量、并发）

## 平台分组

| 组名 | 平台 | 用途 |
|------|------|------|
| `dev` | GitHub, Reddit | 开发者社区 |
| `social` | 小红书, 抖音, B站, YouTube, Twitter, 微博, 知乎 | 社交媒体 |
| `search` | Google, Tavily, DuckDuckGo, Brave, Yahoo, Bing, Wikipedia | 搜索引擎 |
| `books` | Anna's Archive | 电子书 |
| `all` | 所有平台 | 全平台搜索 |

## 常用命令

```bash
# 搜索指定平台
python union_search.py "keyword" --platforms github reddit

# 使用平台组
python union_search.py "keyword" --group social

# 自定义结果数量
python union_search.py "keyword" --limit 5

# JSON 输出
python union_search.py "keyword" --json --pretty

# 保存结果
python union_search.py "keyword" -o results.md
```

## 文档

- [完整文档](UNION_SEARCH_README.md) - 详细功能说明
- [使用示例](EXAMPLES.md) - 实际应用场景
- [测试脚本](test_union_search.py) - 功能测试

## 注意事项

1. 部分平台需要 API 密钥（在 `.env` 文件中配置）
2. 默认每个平台返回 3 条结果
3. 单个平台失败不影响其他平台
4. 建议先用少量平台测试

## 下一步

查看 [EXAMPLES.md](EXAMPLES.md) 了解更多使用场景。
