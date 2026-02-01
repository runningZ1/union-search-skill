# DeepWiki MCP 使用指南

## 简介

DeepWiki MCP 是一个为 GitHub 仓库提供 AI 驱动文档查询的工具，支持文档结构浏览、内容获取和智能问答。

## 配置

### MCP 服务器配置

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

配置后重启 Claude Code 即可使用。

## 三个核心工具

### 1. read_wiki_structure - 获取文档结构

**用途**：查看仓库的文档目录树

**参数**：
- `repoName`: 仓库名称（格式：`owner/repo`）

**示例**：
```
获取 openclaw/openclaw 的文档结构
```

**返回**：层级化的文档目录，包含所有章节和子章节。

---

### 2. read_wiki_contents - 读取完整文档

**用途**：获取仓库的完整文档内容

**参数**：
- `repoName`: 仓库名称（格式：`owner/repo`）

**示例**：
```
读取 facebook/react 的完整文档
```

**返回**：完整的 Markdown 格式文档（可能非常大，会保存到文件）。

---

### 3. ask_question - 智能问答

**用途**：向 AI 提问关于仓库的任何问题

**参数**：
- `repoName`: 仓库名称（格式：`owner/repo`）
- `question`: 你的问题

**示例**：
```
询问 openclaw/openclaw 的架构设计和 Gateway 工作原理
```

**返回**：AI 生成的详细答案，包含引用和相关链接。

## 使用场景

| 场景 | 推荐工具 |
|------|----------|
| 快速了解仓库文档结构 | `read_wiki_structure` |
| 需要完整文档进行深度分析 | `read_wiki_contents` |
| 针对特定问题获取答案 | `ask_question` |
| 架构设计、技术选型研究 | `ask_question` |
| 学习开源项目最佳实践 | `ask_question` |

## 优势

- **即时可用**：配置后无需额外设置
- **高效准确**：直接调用 API，返回结构化数据
- **智能问答**：基于 AI 的上下文理解，提供精准答案
- **完整引用**：答案包含来源引用和相关链接

## 注意事项

1. `read_wiki_contents` 返回的内容可能非常大，会自动保存到文件
2. 仓库名称格式必须是 `owner/repo`（如 `facebook/react`）
3. 仅支持公开的 GitHub 仓库
4. 问答功能支持中英文提问

## 参考资源

- [DeepWiki 官方文档](https://docs.devin.ai/work-with-devin/deepwiki)
- [DeepWiki GitHub](https://github.com/CognitionAI/deepwiki)
- [MCP 协议规范](https://modelcontextprotocol.io/)
