# 谷歌搜索高级指令速查

## 核心运算符

| 符号 | 功能 | 示例 | 说明 |
| :--- | :--- | :--- | :--- |
| `" "` | 精确匹配 | `"machine learning"` | 强制包含完整短语 |
| `-` | 排除 | `python -snake` | 排除包含特定词的结果 |
| `OR` | 或运算 | `docker OR kubernetes` | 包含任意关键词（必须大写） |
| `*` | 通配符 | `"how to * in python"` | 匹配任意单词 |
| `..` | 数值范围 | `camera $50..$100` | 搜索数字/价格范围 |

## 范围限定

| 指令 | 功能 | 示例 | 说明 |
| :--- | :--- | :--- | :--- |
| `site:` | 指定网站 | `site:github.com` | 仅搜索该域名（冒号后无空格） |
| `filetype:` | 文件类型 | `filetype:pdf` | 支持 pdf/doc/ppt/xls |
| `intitle:` | 标题包含 | `intitle:guide` | 关键词必须在标题中 |
| `inurl:` | URL包含 | `inurl:login` | 关键词必须在链接中 |
| `related:` | 相关网站 | `related:bilibili.com` | 查找类似网站 |
| `define:` | 定义 | `define:llm` | 快速查看词义 |

## 时间控制

| 指令 | 功能 | 示例 |
| :--- | :--- | :--- |
| `before:` | 早于 | `python before:2023-01-01` |
| `after:` | 晚于 | `ai after:2023-12-01` |

## 组合示例

```text
# 特定网站资源
site:github.com "union-search" filetype:py

# 排除干扰词
"best laptop" -amazon -ebay 2024

# 官方文档
site:docs.python.org intitle:"asyncio"

# 时间范围+多条件
"python async" site:stackoverflow.com after:2024-01-01 -"deprecated"
```

## 常见错误

| ❌ 错误 | ✅ 正确 | 原因 |
| :--- | :--- | :--- |
| `site: github.com` | `site:github.com` | 冒号后不能有空格 |
| `or` | `OR` | 必须大写 |
| `before:2023` | `before:2023-01-01` | 需完整日期格式 |
