# DeepWiki - GitHub 仓库 AI 文档查询

通过 DeepWiki 查询任何公开 GitHub 仓库的 AI 生成文档，包括架构、API、代码解释等。

## 快速开始

### Web 模式（无需配置）

将仓库 URL 中的 `github.com` 替换为 `deepwiki.com`：
```
github.com/vercel/next.js → deepwiki.com/vercel/next.js
```

## MCP 配置

### Claude Code

```bash
claude mcp add -s user -t http deepwiki https://mcp.deepwiki.com/mcp
```

### Claude Code 配置文件

在 `~/.claude/config.json` 中添加：
```json
{
  "mcpServers": {
    "deepwiki": {
      "url": "https://mcp.deepwiki.com/mcp",
      "transport": "http"
    }
  }
}
```

### Cursor/Windsurf

```json
{
  "mcpServers": {
    "deepwiki": {
      "serverUrl": "https://mcp.deepwiki.com/sse"
    }
  }
}
```

## MCP 工具

配置完成后，以下 MCP 工具可用：

| 工具 | 用途 | 参数 |
|------|------|------|
| `read_wiki_structure` | 获取文档目录结构 | `repoName` |
| `read_wiki_contents` | 读取完整文档内容 | `repoName` |
| `ask_question` | 智能问答 | `repoName`, `question` |

### 使用示例

```
# 获取文档结构
read_wiki_structure("facebook/react")

# 读取完整文档
read_wiki_contents("vercel/next.js")

# 智能问答
ask_question("C4illin/ConvertX", "What is the pricing model?")
```

## 使用场景

| 场景 | 推荐工具 |
|------|----------|
| 快速了解仓库文档结构 | `read_wiki_structure` |
| 需要完整文档进行深度分析 | `read_wiki_contents` |
| 针对特定问题获取答案 | `ask_question` |
| 架构设计、技术选型研究 | `ask_question` |
| 学习开源项目最佳实践 | `ask_question` |

## 备用方案：GitHub API

当 DeepWiki 未覆盖仓库时，使用 GitHub CLI：

```bash
# 仓库概览
gh api repos/owner/repo | jq '{description, language, topics, stars: .stargazers_count}'

# 获取 README
gh api repos/owner/repo/readme --jq '.content' | base64 -d

# 文件结构
gh api repos/owner/repo/git/trees/main?recursive=1 | jq -r '.tree[] | select(.type == "blob") | .path'
```

## 注意事项

- 仓库名称格式：`owner/repo`（如 `facebook/react`）
- 仅支持公开仓库
- `read_wiki_contents` 返回内容较大，会自动保存到文件
- 支持中英文提问

## 资源

- 官网: https://deepwiki.com
- 文档: https://docs.devin.ai/work-with-devin/deepwiki
- GitHub: https://github.com/CognitionAI/deepwiki
