# Union Search - 统一多平台搜索

> 版本: 1.0.0 | 状态: 生产就绪 | 许可: MIT

## 简介

Union Search 是一个强大的多平台搜索聚合工具，能够同时搜索 17+ 个平台并汇总结果。通过统一的接口和并发机制，大幅提升跨平台搜索效率。

### 核心特性

- ✅ **17+ 平台支持** - GitHub、Reddit、小红书、抖音、Bilibili、YouTube 等
- ✅ **并发搜索** - 使用线程池同时搜索多个平台
- ✅ **统一接口** - 所有平台使用相同的调用方式
- ✅ **灵活配置** - 支持平台选择、结果数量、并发数等配置
- ✅ **多种输出** - 支持 Markdown 和 JSON 格式
- ✅ **错误隔离** - 单个平台失败不影响其他平台
- ✅ **生产就绪** - 完善的日志、错误处理和文档

## 快速开始

### 安装

无需安装，直接使用 Python 3.7+ 运行：

```bash
cd scripts/union_search
python union_search.py --help
```

### 基础用法

```bash
# 列出所有平台
python union_search.py --list-platforms

# 搜索开发者平台（GitHub + Reddit）
python union_search.py "Python" --group dev

# 搜索指定平台
python union_search.py "AI" --platforms github reddit xiaohongshu

# 搜索所有平台
python union_search.py "machine learning" --group all --limit 2
```

## 支持的平台

### 开发者与社区
- **GitHub** - 仓库、代码、问题搜索
- **Reddit** - 帖子、子版块搜索

### 社交媒体
- **小红书** - 笔记搜索
- **抖音** - 视频搜索
- **Bilibili** - 视频搜索
- **YouTube** - 视频搜索
- **Twitter** - 帖子搜索
- **微博** - 搜索
- **知乎** - 问答搜索

### 搜索引擎
- **Google** - 搜索
- **Tavily** - AI 搜索
- **DuckDuckGo** - 隐私搜索
- **Brave** - 隐私搜索
- **Yahoo** - 搜索
- **Bing** - 搜索
- **Wikipedia** - 百科搜索

### 其他
- **Anna's Archive** - 电子书搜索

## 平台分组

| 组名 | 平台 | 用途 |
|------|------|------|
| `dev` | GitHub, Reddit | 开发者社区 |
| `social` | 小红书, 抖音, B站, YouTube, Twitter, 微博, 知乎 | 社交媒体 |
| `search` | Google, Tavily, DuckDuckGo, Brave, Yahoo, Bing, Wikipedia | 搜索引擎 |
| `books` | Anna's Archive | 电子书 |
| `all` | 所有平台 | 全平台搜索 |

## 命令行参数

### 必需参数
- `keyword` - 搜索关键词

### 平台选择
- `--platforms`, `-p` - 指定平台列表（空格分隔）
- `--group`, `-g` - 使用平台组（dev/social/search/books/all）

### 搜索配置
- `--limit`, `-l` - 每个平台返回结果数量（默认: 3）
- `--max-workers` - 最大并发数（默认: 5）
- `--timeout` - 超时时间（秒，默认: 60）

### 输出格式
- `--json` - JSON 格式输出
- `--pretty` - 格式化 JSON
- `--markdown` - Markdown 格式输出（默认）
- `-o`, `--output` - 保存到文件

### 其他选项
- `--env-file` - 环境变量文件路径（默认: .env）
- `--list-platforms` - 列出所有平台
- `--verbose`, `-v` - 显示详细日志
- `--version` - 显示版本信息
- `--help`, `-h` - 显示帮助信息

## 使用示例

### 基础搜索

```bash
# 搜索开发者平台
python union_search.py "React" --group dev

# 搜索社交媒体
python union_search.py "美食" --group social --limit 2

# 搜索指定平台
python union_search.py "Python" --platforms github stackoverflow
```

### 高级用法

```bash
# JSON 输出并保存
python union_search.py "AI" --group dev --json --pretty -o results.json

# 详细日志模式
python union_search.py "ML" --group search --verbose

# 自定义并发和超时
python union_search.py "DL" --platforms github reddit --max-workers 10 --timeout 120
```

## 配置

### 环境变量

在项目根目录创建 `.env` 文件：

```bash
# GitHub
GITHUB_TOKEN=your_github_token

# TikHub (小红书、抖音等)
TIKHUB_TOKEN=your_tikhub_token

# Google
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_cse_id

# Tavily
TAVILY_API_KEY=your_tavily_key
```

详细配置请参考 [API 凭据获取指南](../../references/api_credentials.md)。

## 输出格式

### Markdown 格式（默认）

```markdown
# 联合搜索结果: Python

**搜索时间**: 2026-02-16T22:00:00
**平台数量**: 2
**成功**: 2 | **失败**: 0
**总结果数**: 6

---

## GITHUB

✅ 找到 3 条结果

### 1. python/cpython
- **链接**: https://github.com/python/cpython
- **描述**: The Python programming language
...
```

### JSON 格式

```json
{
  "keyword": "Python",
  "platforms": ["github", "reddit"],
  "limit_per_platform": 3,
  "timestamp": "2026-02-16T22:00:00",
  "results": {
    "github": {
      "platform": "github",
      "success": true,
      "items": [...],
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

## 性能优化

### 并发配置

```bash
# 低并发（节省资源）
python union_search.py "keyword" --max-workers 2

# 高并发（更快速度）
python union_search.py "keyword" --max-workers 10
```

### 结果数量

```bash
# 快速预览（每个平台 1 条）
python union_search.py "keyword" --limit 1

# 详细结果（每个平台 5 条）
python union_search.py "keyword" --limit 5
```

## 故障排查

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 平台搜索失败 | 检查 API 密钥配置 |
| 超时错误 | 增加 `--timeout` 值 |
| 并发错误 | 减少 `--max-workers` 值 |
| 无结果 | 使用 `--verbose` 查看详细日志 |

### 调试模式

```bash
# 启用详细日志
python union_search.py "keyword" --verbose

# 查看版本信息
python union_search.py --version
```

## 架构设计

### 核心组件

1. **平台适配器** - 统一各平台的搜索接口
2. **并发引擎** - ThreadPoolExecutor 实现并发搜索
3. **错误隔离** - 单个平台失败不影响其他
4. **格式化器** - 支持多种输出格式

### 工作流程

```
用户输入 → 参数解析 → 平台选择 → 并发搜索 → 结果汇总 → 格式化输出
```

## 扩展开发

### 添加新平台

1. 在 `PLATFORM_MODULES` 中添加平台配置
2. 实现 `_search_<platform>` 函数
3. 更新平台分组（可选）

示例：

```python
# 1. 添加配置
PLATFORM_MODULES["newplatform"] = {
    "module": "newplatform.search",
    "function": "search_newplatform",
    "description": "New Platform 搜索"
}

# 2. 实现搜索函数
def _search_newplatform(keyword: str, limit: int, **kwargs) -> List[Dict]:
    # 调用平台搜索脚本
    ...
    return results
```

## 版本历史

### v1.0.0 (2026-02-16)
- ✅ 初始发布
- ✅ 支持 17+ 个平台
- ✅ 并发搜索机制
- ✅ 多种输出格式
- ✅ 完善的错误处理
- ✅ 详细的文档

## 许可证

MIT License

## 相关文档

- [快速开始指南](QUICKSTART.md)
- [使用示例](EXAMPLES.md)
- [项目总结](SUMMARY.md)
- [API 凭据获取](../../references/api_credentials.md)
- [速率限制说明](../../references/rate_limits.md)
- [问题排查指南](../../references/troubleshooting.md)

## 支持

如有问题或建议，请查看：
- 项目文档
- 使用 `--help` 查看帮助
- 使用 `--verbose` 查看详细日志

---

**版本**: 1.0.0 | **状态**: 生产就绪 | **最后更新**: 2026-02-16
