# DeepWiki 功能测试报告

## 功能概述

DeepWiki 是一个强大的工具，可以通过 AI 直接查询 GitHub 仓库的文档和内容，**无需下载到本地**。它为 50,000+ 热门 GitHub 仓库提供 AI 生成的文档。

## 主要优势

1. **远程查询**：无需克隆仓库到本地，直接在线查询
2. **AI 驱动**：使用 AI 理解和解释代码、架构
3. **快速访问**：即时获取仓库结构、API 文档、代码解释
4. **多种方式**：支持 WebFetch 和 MCP 两种访问方式

## 使用方式

### 方式 1: WebFetch（推荐，立即可用）

最简单的方式，无需任何配置：

```bash
WebFetch https://deepwiki.com/owner/repo "你的问题"
```

**示例**：
```bash
WebFetch https://deepwiki.com/vercel/next.js "请总结 Next.js 的核心架构和主要特性"
```

**测试结果**：✅ 成功
- 成功获取了 Next.js 的详细架构信息
- AI 总结了核心特性、渲染策略、路由系统等
- 响应速度快，内容准确

### 方式 2: MCP 工具（需配置）

配置 MCP 服务器后，可以使用专门的工具：

**配置命令**：
```bash
claude mcp add -s user -t http deepwiki https://mcp.deepwiki.com/mcp
```

**可用工具**：
- `mcp__deepwiki__read_wiki_structure` - 获取仓库结构
- `mcp__deepwiki__read_wiki_contents` - 获取文档内容
- `mcp__deepwiki__ask_question` - 向 AI 提问

**配置状态**：✅ 已成功配置

## 使用场景

1. **快速了解新项目**：无需下载，直接查询项目架构
2. **API 文档查询**：快速查找 API 使用方法
3. **代码理解**：询问特定功能的实现原理
4. **架构分析**：了解项目的整体结构和设计

## 限制

- 仅支持公开仓库（私有仓库需要 Devin 账号）
- 覆盖 50,000+ 热门仓库，不是所有仓库都已索引
- 对于未索引的仓库，可以回退到 GitHub API

## 最佳实践

1. **优先使用 WebFetch**：简单直接，无需配置
2. **提出具体问题**：越具体的问题，AI 回答越准确
3. **检查仓库是否已索引**：热门项目覆盖更好
4. **备用方案**：未索引的仓库使用 GitHub API

## 与 GitHub 搜索的集成

DeepWiki 是 GitHub 搜索模块的重要补充：
- **GitHub 搜索**：查找仓库、代码、问题
- **DeepWiki**：深入理解仓库内容和架构

两者结合使用，可以实现：
1. 用 GitHub 搜索找到目标仓库
2. 用 DeepWiki 深入了解仓库内容
3. 无需下载即可完成调研

## 测试结论

✅ **功能正常**：WebFetch 方式测试成功
✅ **MCP 已配置**：DeepWiki MCP 服务器已添加
✅ **响应准确**：AI 生成的文档质量高
✅ **使用便捷**：无需下载仓库即可查询

## 推荐使用

强烈推荐在以下场景使用 DeepWiki：
- 技术选型时快速了解框架
- 学习开源项目的架构设计
- 查找 API 使用方法
- 理解复杂代码的实现原理

DeepWiki 是一个非常实用的工具，大大提高了 GitHub 仓库的调研效率！
