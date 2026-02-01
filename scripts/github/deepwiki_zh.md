# DeepWiki - 仓库文档查询

通过 DeepWiki 查询任何公开 GitHub 仓库的 AI 生成文档。

## 概述

DeepWiki (deepwiki.com) 为 GitHub 仓库提供 AI 生成的文档，包括：
- 仓库结构和架构
- API 文档
- 代码解释
- 交互式图表

## 快速开始

**URL 模式**：将任何仓库 URL 中的 `github.com` 替换为 `deepwiki.com`：
- `github.com/vercel/next.js` → `deepwiki.com/vercel/next.js`

## MCP 服务器设置

DeepWiki 提供免费的 MCP 服务器，公开仓库无需认证。

### 添加到 Claude Code（一次性设置）

```bash
claude mcp add -s user -t http deepwiki https://mcp.deepwiki.com/mcp
```

### 对于 Cursor/Windsurf

添加到 MCP 配置：
```json
{
  "mcpServers": {
    "deepwiki": {
      "serverUrl": "https://mcp.deepwiki.com/sse"
    }
  }
}
```

## 可用的 MCP 工具

配置完成后，以下工具可用：

| 工具 | 用途 |
|------|------|
| `read_wiki_structure` | 获取仓库的文档主题/结构 |
| `read_wiki_contents` | 检索实际文档内容 |
| `ask_question` | 向 AI 提问关于仓库的问题 |

## 使用示例

### 通过 WebFetch（立即可用）

```bash
# 获取文档概览
WebFetch https://deepwiki.com/owner/repo "总结架构"

# 示例
WebFetch https://deepwiki.com/vercel/next.js "路由是如何工作的？"
```

### 通过 MCP（设置后）

直接使用 MCP 工具：
- `mcp__deepwiki__read_wiki_structure` - 获取仓库结构
- `mcp__deepwiki__read_wiki_contents` - 获取文档
- `mcp__deepwiki__ask_question` - 提问

## 备用方案：GitHub + AI

如果 DeepWiki 没有覆盖某个仓库，使用 GitHub API：

### 获取仓库概览

```bash
gh api repos/owner/repo | jq '{description, language, topics, stars: .stargazers_count}'
```

### 获取 README

```bash
gh api repos/owner/repo/readme --jq '.content' | base64 -d
```

### 获取文件结构

```bash
gh api repos/owner/repo/git/trees/main?recursive=1 | \
  jq -r '.tree[] | select(.type == "blob") | .path' | head -50
```

## 通信协议

支持两种协议：
- **SSE** at `https://mcp.deepwiki.com/sse` - 官方 MCP 规范
- **HTTP** at `https://mcp.deepwiki.com/mcp` - Cloudflare/OpenAI 兼容

## 最佳实践

1. **优先使用 WebFetch** - 无需 MCP 设置即可工作
2. **检查仓库是否已索引** - 热门仓库覆盖更好
3. **提出具体问题** - DeepWiki 擅长针对性查询
4. **备用 GitHub** - 用于未索引或私有仓库

## 限制

- **仅限公开仓库** - 私有仓库需要 Devin 账号
- **覆盖范围不同** - 已索引 50,000+ 热门仓库
- **无需认证** - 无法访问私有文档

## 资源

- 网站: https://deepwiki.com
- 文档: https://docs.devin.ai/work-with-devin/deepwiki
- GitHub: https://github.com/CognitionAI/deepwiki
