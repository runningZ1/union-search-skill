# 微信公众号文章搜索（JavaScript 版本）

通过搜狗微信搜索获取微信公众号文章，支持多页搜索、真实 URL 解析等功能。

## 功能特点

- **无需 API Key**：直接使用搜狗微信搜索接口
- **多页搜索**：支持分页获取最多 50 条结果
- **真实 URL 解析**：可将搜狗中间链接解析为微信文章真实地址
- **详细结果**：返回标题、链接、概要、发布时间、公众号名称等信息
- **User-Agent 池**：20 个不同 UA 随机切换，降低被封禁风险

## 安装依赖

```bash
npm install cheerio
```

## 使用方法

### 基本搜索

```bash
node scripts/wechat/search_wechat.js "人工智能"
```

### 指定结果数量

```bash
node scripts/wechat/search_wechat.js "ChatGPT" -n 20
```

### 保存结果为 JSON 文件

```bash
node scripts/wechat/search_wechat.js "AI" -n 10 -o result.json
```

### 解析真实 URL

```bash
node scripts/wechat/search_wechat.js "人工智能" -n 5 -r
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必填） | - |
| `-n, --num` | 返回结果数量（最大 50） | 10 |
| `-o, --output` | 输出 JSON 文件路径 | - |
| `-r, --resolve-url` | 解析真实微信文章 URL | false |

## 输出格式

```json
{
  "query": "人工智能",
  "total": 10,
  "articles": [
    {
      "title": "文章标题",
      "url": "文章链接",
      "summary": "文章概要",
      "datetime": "2024-01-15 10:30:00",
      "date_text": "2024 年 01 月 15 日",
      "date_description": "2 天前",
      "source": "公众号名称"
    }
  ]
}
```

## 注意事项

- **反爬虫限制**：搜狗微信有严格的反爬虫机制，可能导致部分请求失败
- **真实 URL 解析**：开启 `-r` 参数会显著增加请求时间（每个链接需额外请求）
- **使用频率**：建议不要过于频繁地请求，避免 IP 被封禁
- **仅供学习**：本工具仅供学习和研究使用

## 常见问题

### 结果为空
- 尝试更换关键词
- 减少特殊字符使用
- 稍后重试

### 解析真实 URL 失败
- 这是正常现象（反爬限制）
- 可使用浏览器手动打开搜狗链接跳转获取真实地址

## 与其他版本的区别

| 版本 | 语言 | 特点 |
|------|------|------|
| `wechat_no_api.py` | Python | 基于项目统一引擎架构，支持基础搜索 |
| `search_wechat.js` | JavaScript | 功能更完整，支持多页、真实 URL 解析、Cookie 管理 |

## 集成到 union-search

此脚本可作为独立工具使用，也可通过 `module.exports` 集成到 `union_search.py` 中作为搜索引擎之一。
