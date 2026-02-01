# GitHub Search

GitHub 搜索模块 - 搜索 GitHub 仓库、代码和问题

## 功能特性

- **仓库搜索**: 按语言、星标、主题、许可证等条件搜索仓库
- **代码搜索**: 跨所有公共仓库搜索代码片段
- **问题搜索**: 搜索问题和 Pull Request
- **速率限制检查**: 查看当前 API 配额使用情况
- **多种输出格式**: Text、JSON、Markdown
- **自动存档**: 保存原始 API 响应到 `responses/` 目录

## 安装依赖

```bash
pip install requests
```

## 配置

### 获取 GitHub Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择权限范围（公共搜索无需特殊权限）
4. 复制生成的 token

### 配置方式

**方式 1: 命令行参数**
```bash
python scripts/github/github_search.py repo "query" --token YOUR_TOKEN
```

**方式 2: 环境变量**
```bash
export GITHUB_TOKEN=YOUR_TOKEN
python scripts/github/github_search.py repo "query"
```

**方式 3: .env 文件** (推荐)
```bash
# 在 union-search-skill 目录下创建 .env 文件
GITHUB_TOKEN=your_token_here
```

## 使用方法

### 仓库搜索

```bash
# 基础搜索
python scripts/github/github_search.py repo "machine learning"

# 按语言筛选
python scripts/github/github_search.py repo "web framework" --language python

# 按星标筛选
python scripts/github/github_search.py repo "django" --stars ">5000"

# 组合筛选
python scripts/github/github_search.py repo "cli" --language go --stars ">1000" --limit 10

# 按星标排序
python scripts/github/github_search.py repo "react" --sort stars --limit 10
```

### 代码搜索

```bash
# 搜索代码片段
python scripts/github/github_search.py code "def main" --language python

# 在特定仓库中搜索
python scripts/github/github_search.py code "OAuth2" --repo "flask/flask"

# 按文件扩展名搜索
python scripts/github/github_search.py code "import React" --extension jsx

# 按路径搜索
python scripts/github/github_search.py code "database" --path "config/"
```

### 问题搜索

```bash
# 搜索问题
python scripts/github/github_search.py issue "bug" --state open

# 按标签筛选
python scripts/github/github_search.py issue "help wanted" --label "good first issue"

# 仅搜索 PR
python scripts/github/github_search.py issue "feature" --is-pr --state open

# 在特定仓库中搜索
python scripts/github/github_search.py issue "performance" --repo "owner/repo"
```

### 速率限制检查

```bash
python scripts/github/github_search.py rate-limit
```

### 输出格式

```bash
# JSON 格式
python scripts/github/github_search.py repo "django" --format json

# Markdown 格式
python scripts/github/github_search.py repo "vue" --format markdown

# 保存到文件
python scripts/github/github_search.py repo "python" --format markdown -o results.md
```

### 保存原始响应

```bash
python scripts/github/github_search.py repo "django" --save-raw
```

原始响应将保存到 `responses/github_repo_TIMESTAMP.json`

## 命令参数

### 仓库搜索 (repo)

| 参数 | 描述 |
|------|------|
| `query` | 搜索关键词 (必需) |
| `--sort` | 排序字段: stars, forks, help-wanted-issues, updated |
| `--order` | 排序顺序: asc, desc (默认: desc) |
| `--limit` | 最大结果数 (默认: 30, 最大: 1000) |
| `--language` | 编程语言 |
| `--user` | 用户/组织 |
| `--stars` | 星标数 (例: ">1000", "100..500") |
| `--forks` | 分支数 |
| `--topic` | 主题标签 |
| `--license` | 许可证 (例: "mit", "apache-2.0") |
| `--created` | 创建日期 (例: ">2024-01-01") |
| `--pushed` | 最后推送日期 |
| `--archived` | 归档状态: true, false |

### 代码搜索 (code)

| 参数 | 描述 |
|------|------|
| `query` | 搜索关键词 (必需) |
| `--sort` | 排序字段: indexed (仅此选项) |
| `--order` | 排序顺序: asc, desc (默认: desc) |
| `--limit` | 最大结果数 (默认: 30, 最大: 1000) |
| `--language` | 编程语言 |
| `--repo` | 仓库 (格式: owner/repo) |
| `--user` | 用户/组织 |
| `--path` | 文件路径 |
| `--extension` | 文件扩展名 (例: "js", "py") |

### 问题搜索 (issue)

| 参数 | 描述 |
|------|------|
| `query` | 搜索关键词 (必需) |
| `--sort` | 排序字段: comments, reactions, interactions, created, updated |
| `--order` | 排序顺序: asc, desc (默认: desc) |
| `--limit` | 最大结果数 (默认: 30, 最大: 1000) |
| `--repo` | 仓库 (格式: owner/repo) |
| `--user` | 用户/组织 |
| `--state` | 状态: open, closed |
| `--author` | 作者用户名 |
| `--assignee` | 受让人用户名 |
| `--label` | 标签 |
| `--milestone` | 里程碑 |
| `--is-pr` | 仅显示 Pull Request |
| `--is-issue` | 仅显示 Issue |
| `--created` | 创建日期 (例: ">2024-01-01") |
| `--updated` | 更新日期 |

### 全局参数

| 参数 | 描述 |
|------|------|
| `--token` | GitHub Personal Access Token |
| `--format` | 输出格式: text, json, markdown (默认: text) |
| `--output, -o` | 输出文件路径 |
| `--save-raw` | 保存原始响应到 responses/ 目录 |

## API 速率限制

GitHub API 有速率限制：

- **已认证**: 30 次搜索/分钟, 5000 次核心请求/小时
- **未认证**: 10 次搜索/分钟, 60 次核心请求/小时

运行 `rate-limit` 命令检查当前限制：

```bash
python scripts/github/github_search.py rate-limit
```

## 测试

运行测试脚本验证功能：

```bash
python scripts/github/test_github_search.py
```

## 输出示例

### Text 格式 (默认)

```
================================================================================
GitHub Repositories Results
Showing 3 of 710421 results
================================================================================

📦 django/django
   ⭐ 86634 | 🍴 33577 | 💻 Python
   📝 The Web framework for perfectionists with deadlines.
   🔗 https://github.com/django/django

📦 getsentry/sentry
   ⭐ 43045 | 🍴 4583 | 💻 Python
   📝 Developer-first error tracking and performance monitoring
   🔗 https://github.com/getsentry/sentry
```

### Markdown 格式

```markdown
# GitHub Search Results

**Showing 3 of 1090 results**

## Repositories

### [rwf2/Rocket](https://github.com/rwf2/Rocket)
⭐ 25643 | 🍴 1620 | 💻 Rust
A web framework for Rust.
```

## 错误处理

| 错误 | 描述 | 解决方案 |
|------|------|----------|
| Authentication failed | Token 无效 | 检查 GITHUB_TOKEN 环境变量或 --token 参数 |
| Rate limit exceeded | 超出速率限制 | 等待限制重置（使用 rate-limit 命令检查） |
| Query validation failed | 查询语法错误 | 检查查询格式和筛选器语法 |
| Connection error | 网络问题 | 检查网络连接 |
