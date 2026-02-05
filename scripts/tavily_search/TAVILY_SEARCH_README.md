# Tavily Search

为 LLM 应用优化的 AI 驱动搜索引擎，提供实时网络搜索和 AI 生成答案。

## 功能特性

- ✅ 实时网络搜索，带 AI 生成答案
- ✅ 多种搜索深度（basic、advanced、fast）
- ✅ 特定主题搜索（general、news、finance）
- ✅ 可选的 AI 答案摘要
- ✅ 多种输出格式（文本、JSON）

## 安装

```bash
pip install tavily-python python-dotenv
```

## 配置

### 获取 API Key

1. 访问 [Tavily.com](https://tavily.com) 注册账号（有免费套餐）
2. 获取 API Key
3. 在项目根目录的 `.env` 文件中添加：
   ```bash
   TAVILY_API_KEY=tvly-your_api_key
   ```

## 使用示例

### 基础搜索

```bash
# 基础搜索
python scripts/tavily_search/tavily_search.py "AI latest developments" --max-results 5

# 新闻搜索
python scripts/tavily_search/tavily_search.py "technology news" --topic news --max-results 10
```

### 高级搜索

```bash
# 带 AI 答案的高级搜索
python scripts/tavily_search/tavily_search.py "quantum computing" --search-depth advanced --include-answer --max-results 5

# 快速搜索
python scripts/tavily_search/tavily_search.py "Python vs JavaScript" --search-depth fast --max-results 3
```

### 输出格式

```bash
# JSON 输出
python scripts/tavily_search/tavily_search.py "machine learning" --json --pretty
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `--max-results` | 最大结果数 | 5 |
| `--search-depth` | 搜索深度（basic/advanced/fast） | basic |
| `--topic` | 主题（general/news/finance） | general |
| `--include-answer` | 包含 AI 生成的答案 | False |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON 输出 | False |

## 搜索深度说明

- **basic**：标准搜索，平衡速度和质量
- **advanced**：深度搜索，更全面的结果
- **fast**：快速搜索，优先速度

## 输出信息

- AI 生成的答案摘要（如果启用）
- 搜索结果，包含标题、URL 和内容摘要
- 结果总数

## 注意事项

1. **API 配额**：免费套餐有请求限制，查看 [定价页面](https://tavily.com/pricing)
2. **搜索深度**：advanced 模式消耗更多配额
3. **AI 答案**：启用 `--include-answer` 会增加响应时间

## 相关链接

- [Tavily 官方文档](https://docs.tavily.com/)
- [Python SDK 文档](https://github.com/tavily-ai/tavily-python)
