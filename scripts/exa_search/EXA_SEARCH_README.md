# Exa Search

基于 Exa AI 的神经搜索服务，提供网页搜索、代码搜索、公司研究、人物搜索和深度研究功能。无需 API 密钥。

## 功能特性

- ✅ 网页搜索 - 实时网络信息检索
- ✅ 代码搜索 - GitHub、Stack Overflow 代码示例
- ✅ 公司研究 - 商业信息和新闻
- ✅ 人物搜索 - 专业人士个人资料
- ✅ 深度研究 - AI 驱动的深入分析报告
- ✅ 网页抓取 - 获取特定网页的完整内容

## 配置

### 前提条件

1. 安装 mcporter：
```bash
npm install -g mcporter
```

2. 配置 Exa MCP：
```bash
mcporter config add exa "https://mcp.exa.ai/mcp?tools=web_search_exa,web_search_advanced_exa,get_code_context_exa,crawling_exa,company_research_exa,people_search_exa,deep_researcher_start,deep_researcher_check"
```

3. 验证配置：
```bash
mcporter list exa
```

## 使用示例

### 网页搜索

```bash
# 基础搜索
python scripts/exa_search/exa_search.py web "AI latest developments"

# 快速搜索
python scripts/exa_search/exa_search.py web "Python tutorial" --type fast

# 深度搜索
python scripts/exa_search/exa_search.py web "machine learning" --type deep
```

### 代码搜索

```bash
# 搜索代码示例
python scripts/exa_search/exa_search.py code "React hooks examples" --tokens 3000
```

### 公司研究

```bash
# 公司信息搜索
python scripts/exa_search/exa_search.py company "Anthropic"

# 带结果数限制
python scripts/exa_search/exa_search.py company "OpenAI" --max-results 10
```

### 人物搜索

```bash
# 搜索专业人士
python scripts/exa_search/exa_search.py people "Sam Altman"
```

### 网页抓取

```bash
# 抓取网页内容
python scripts/exa_search/exa_search.py crawl "https://example.com" --max-chars 5000
```

### 深度研究

```bash
# 启动深度研究（返回研究 ID）
python scripts/exa_search/exa_search.py deep "latest advances in quantum computing"

# 使用研究 ID 检查结果
python scripts/exa_search/exa_search.py check "r_xxxxxxxxxxxxx"
```

## 命令行参数

### 通用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `type` | 搜索类型 (web/code/company/people/crawl/deep/check) | web |
| `query` | 搜索关键词或 URL | - |
| `--max-results` | 最大结果数 | 8 |
| `--tokens` | 代码搜索的 token 数量 | 5000 |
| `--max-chars` | 网页抓取的最大字符数 | 3000 |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON 输出 | False |

### 搜索类型特定参数

**web 搜索:**
- `--type`: fast (快速) / deep (深度) / auto (自动)

**crawl 抓取:**
- `--max-chars`: 最大字符数 (默认 3000)

**deep 研究:**
- `--model`: exa-research-fast / exa-research / exa-research-pro

**check 检查:**
- `research_id`: 研究任务 ID

## 输出格式

搜索结果包含：
- 标题
- URL 链接
- 内容摘要
- 出版日期（如果适用）

## 故障排除

### MCP 显示 offline

重新配置：
```bash
mcporter config add exa "https://mcp.exa.ai/mcp?tools=web_search_exa,web_search_advanced_exa,get_code_context_exa,crawling_exa,company_research_exa,people_search_exa,deep_researcher_start,deep_researcher_check"
```

### mcporter 未找到

```bash
npm install -g mcporter
```

## 相关链接

- [Exa MCP Server GitHub](https://github.com/exa-labs/exa-mcp-server)
- [Exa npm](https://www.npmjs.com/package/exa-mcp-server)
- [Exa Docs](https://exa.ai/docs)
