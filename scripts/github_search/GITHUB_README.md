# GitHub Search

搜索 GitHub 仓库、代码和问题

## 安装

```bash
pip install requests
```

## 配置

在根目录 `.env` 文件中添加：
```bash
GITHUB_TOKEN=your_github_token_here
```

获取 Token: https://github.com/settings/tokens（公共搜索无需特殊权限）

## 使用示例

### 仓库搜索
```bash
python scripts/github_search/github_search.py repo "machine learning" --language python --stars ">1000"
```

### 代码搜索
```bash
python scripts/github_search/github_search.py code "def main" --language python
```

### 问题搜索
```bash
python scripts/github_search/github_search.py issue "bug" --state open --label "good first issue"
```

### 速率限制检查
```bash
python scripts/github_search/github_search.py rate-limit
```

## 主要参数

**仓库搜索**: `--language`, `--stars`, `--forks`, `--user`, `--topic`, `--license`, `--sort`

**代码搜索**: `--language`, `--repo`, `--path`, `--extension`

**问题搜索**: `--state`, `--is-pr`, `--is-issue`, `--author`, `--label`, `--repo`

**通用参数**: `--format` (text/json/markdown), `--output`, `--save-raw`, `--limit`

## API 速率限制

- 已认证: 30 次搜索/分钟, 5000 次核心请求/小时
- 未认证: 10 次搜索/分钟, 60 次核心请求/小时

---

## 🆕 DeepWiki - AI 仓库文档查询

**无需下载仓库，直接通过 AI 查询仓库内容！**

### 快速使用

```bash
WebFetch https://deepwiki.com/owner/repo "你的问题"
```

**示例**：
```bash
WebFetch https://deepwiki.com/vercel/next.js "请总结 Next.js 的核心架构"
WebFetch https://deepwiki.com/facebook/react "React 的 Fiber 架构是如何工作的？"
```

### 功能特点

- ✅ **远程查询**：无需克隆仓库到本地
- ✅ **AI 驱动**：智能理解代码和架构
- ✅ **即时响应**：快速获取文档和解释
- ✅ **覆盖广泛**：支持 50,000+ 热门仓库

### 使用场景

1. 快速了解新项目的架构
2. 查询 API 使用方法
3. 理解代码实现原理
4. 技术选型调研
