# 知乎搜索模块

基于 Playwright 的知乎搜索信息获取模块，支持搜索问题、回答、文章等内容。

## 功能特性

- **多种搜索类型**：支持综合搜索、文章搜索、用户搜索
- **灵活排序**：支持默认排序、相关性排序、时间排序、热门排序
- **完整内容获取**：可选择获取完整的回答/文章内容
- **评论数据**：支持获取评论数据
- **多种输出格式**：文本终端、JSON、Markdown
- **反爬策略**：Playwright 浏览器自动化 + 请求签名

## 安装

### 1. 安装依赖

```bash
pip install -r scripts/zhihu/requirements.txt
```

### 2. 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 3. 配置 Cookie

在项目根目录的 `.env` 文件中添加：

```bash
ZHIHU_COOKIE=your_cookie_string_here
```

**获取 Cookie 的方法：**
1. 登录知乎网站 (https://www.zhihu.com)
2. 打开浏览器开发者工具（F12）
3. 切换到 "Network" 标签
4. 刷新页面
5. 找到任意请求，查看 Request Headers 中的 Cookie
6. 复制整个 Cookie 字符串到 `.env` 文件

## 使用方法

### 基本用法

```bash
# 搜索问题
python scripts/zhihu/zhihu_search.py "Python 异步编程"

# 搜索文章
python scripts/zhihu/zhihu_search.py "机器学习" --type article

# 按热门排序
python scripts/zhihu/zhihu_search.py "深度学习" --sort votes --limit 20
```

### 获取完整内容

```bash
# 获取完整内容
python scripts/zhihu/zhihu_search.py "LLM" --full-content --limit 5

# 包含评论数据
python scripts/zhihu/zhihu_search.py "RAG" --with-comments --limit 3
```

### 输出格式

```bash
# JSON 输出
python scripts/zhihu/zhihu_search.py "AI" --json --pretty

# Markdown 输出
python scripts/zhihu/zhihu_search.py "Agent" --markdown -o output.md

# 保存原始响应
python scripts/zhihu/zhihu_search.py "大模型" --save-raw
```

### 调试模式

```bash
# 显示浏览器窗口（查看实际运行过程）
python scripts/zhihu/zhihu_search.py "测试" --no-headless
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `keyword` | 搜索关键词（必需） | - |
| `--type` | 搜索类型 (content/article/people) | content |
| `--sort` | 排序方式 (default/relevance/time/votes) | default |
| `--limit` | 结果数量 | 10 |
| `--full-content` | 获取完整内容 | false |
| `--with-comments` | 包含评论数据 | false |
| `--json` | JSON 格式输出 | false |
| `--pretty` | 格式化 JSON | false |
| `--markdown` | Markdown 格式输出 | false |
| `-o, --output` | 输出文件路径 | - |
| `--save-raw` | 保存原始响应 | false |
| `--no-headless` | 显示浏览器窗口 | false |

## 输出数据结构

```json
{
  "rank": 1,
  "id": "123456789",
  "type": "answer",
  "title": "问题标题",
  "excerpt": "回答摘要...",
  "author": {
    "id": "user_id",
    "name": "用户名",
    "url": "https://www.zhihu.com/people/...",
    "headline": "个人简介"
  },
  "url": "https://www.zhihu.com/question/xxx/answer/xxx",
  "stats": {
    "votes": 1000,
    "comments": 50
  },
  "created_at": "2024-01-01",
  "updated_at": "2024-01-15",
  "question": {
    "id": "question_id",
    "title": "问题标题"
  },
  "topics": ["话题1", "话题2"]
}
```

## 注意事项

1. **Cookie 时效性**：Cookie 需要定期更新，建议每周检查一次
2. **请求频率**：避免频繁请求，建议每次搜索间隔至少 1 秒
3. **法律合规**：仅用于学习和研究，遵守知乎服务条款
4. **错误处理**：
   - 403 错误：通常需要更新 Cookie
   - 429 错误：请求过于频繁，请稍后再试

## 目录结构

```
scripts/zhihu/
├── zhihu_search.py         # 主入口脚本
├── core.py                 # 核心搜索客户端
├── client.py               # API 客户端
├── extractor.py            # 数据提取器
├── fetcher.py              # 完整内容获取器
├── signature.py            # 签名生成器
├── field.py                # 枚举定义
├── exception.py            # 自定义异常
├── requirements.txt        # 依赖声明
├── README.md               # 模块文档
├── responses/              # 原始响应存档
└── libs/                   # 第三方脚本
    └── stealth.min.js      # 反检测脚本
```

## 故障排除

### Playwright 安装失败

```bash
# 尝试使用国内镜像
set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
playwright install chromium
```

### Cookie 无效

1. 检查 Cookie 格式是否正确
2. 尝试重新登录知乎获取新的 Cookie
3. 确保包含关键的 Cookie 字段（如 `d_c0`）

### 签名错误

如果遇到签名相关的错误（x-zse-96），可能需要：
1. 更新 `signature.py` 中的签名算法
2. 参考 MediaCrawler 项目的最新实现

## 参考

- [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) - 媒体爬虫项目
- [Playwright Python 文档](https://playwright.dev/python/)
- [知乎 x-zse-96 签名分析](https://juejin.cn/post/7031085262176256036)

## 版本历史

- **v1.0.0** (2024-02-01)
  - 初始版本
  - 支持基础搜索功能
  - 支持完整内容获取
  - 支持多种输出格式
