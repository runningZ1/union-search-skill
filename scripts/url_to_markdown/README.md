# URL to Markdown - 双引擎网页内容提取

将网页 URL 转换为 LLM 友好的 Markdown 内容。

## 架构说明

本模块采用**双引擎架构**，提供高可用的网页内容提取服务：

| 引擎 | 类型 | 优先级 | 特点 |
|------|------|--------|------|
| **Jina AI** | API | 首选 | 快速、稳定、免费、无需本地依赖 |
| **Defuddle** | 本地 | 备选 | 无速率限制、完全本地、需 Node.js |

### 自动降级逻辑

```
用户请求
    ↓
尝试 Jina AI API
    ↓
成功 → 返回结果
    ↓
失败 → 自动切换到 Defuddle
    ↓
返回结果（或报错）
```

## 安装说明

### 基本要求

- Python 3.8+
- `requests` 库
- `python-dotenv` 库

### Defuddle 引擎（可选）

Defuddle 作为备选引擎，在 Jina 失败时自动使用。需要：

- Node.js 18+
- npm

首次使用时会自动检查 Defuddle 是否可用。

## 使用方法

### Python API

#### 基本使用

```python
from scripts.url_to_markdown import UrlToMarkdown, fetch_url_as_markdown

# 便捷函数（推荐）
content = fetch_url_as_markdown("https://example.com/article")
print(content)

# 高级用法
client = UrlToMarkdown()
result = client.fetch(
    url="https://example.com/article",
    with_images=True,
    timeout=30
)
print(result["title"])
print(result["content"])
print(result["_engine_used"])  # 显示使用的引擎
```

#### 指定引擎

```python
# 仅使用 Jina（不启用降级）
client_jina = UrlToMarkdown(prefer_engine="jina", enable_fallback=False)

# 仅使用 Defuddle（不启用降级）
client_defuddle = UrlToMarkdown(prefer_engine="defuddle", enable_fallback=False)

# 优先 Defuddle，失败时使用 Jina
client_defuddle_first = UrlToMarkdown(prefer_engine="defuddle", enable_fallback=True)

# 自动模式（默认）- 优先 Jina，失败时使用 Defuddle
client_auto = UrlToMarkdown(prefer_engine="auto", enable_fallback=True)
```

#### 高级参数

```python
result = client.fetch(
    url="https://example.com",
    with_images=True,           # 包含图片
    with_links=True,            # 包含链接
    with_generated_alt=True,    # 生成图片 alt 文本（较慢）
    target_selector="article",  # 只提取指定区域
    wait_for_selector=".content",  # 等待元素加载
    no_cache=True,              # 绕过缓存
    timeout=60,                 # 超时时间
)
```

### CLI 使用

```bash
# 基本使用
python scripts/url_to_markdown/url_to_markdown.py https://example.com

# JSON 输出
python scripts/url_to_markdown/url_to_markdown.py https://example.com --json

# 详细输出
python scripts/url_to_markdown/url_to_markdown.py https://example.com --verbose

# 指定引擎
python scripts/url_to_markdown/url_to_markdown.py https://example.com --prefer-engine jina
python scripts/url_to_markdown/url_to_markdown.py https://example.com --prefer-engine defuddle

# 禁用自动降级
python scripts/url_to_markdown/url_to_markdown.py https://example.com --no-fallback

# 保存到文件
python scripts/url_to_markdown/url_to_markdown.py https://example.com -o output.md
```

## 输出格式

### 标准输出

```python
{
    "url": "https://example.com",
    "title": "Example Domain",
    "content": "Markdown 内容...",
    "markdown": "Markdown 内容...",
    "_engine_used": "jina",  # 显示使用的引擎
}
```

### JSON 输出（完整元数据）

```python
{
    "url": "https://example.com",
    "title": "Example Domain",
    "content": "...",
    "description": "...",
    "domain": "example.com",
    "favicon": "https://example.com/favicon.ico",
    "image": "",
    "author": "Author Name",
    "published": "2024-01-15",
    "meta_tags": [...],
    "markdown": "...",
    "_engine_used": "jina",
}
```

## 引擎对比

### Jina AI Reader API

**优点：**
- 快速响应
- 无需本地依赖
- 支持动态渲染页面
- 免费版无需 API Key

**缺点：**
- 免费版有速率限制（20 RPM）
- 依赖外部 API

**适用场景：**
- 日常使用
- 动态页面（SPA）
- 快速原型开发

### Defuddle

**优点：**
- 完全免费，无速率限制
- 本地运行，隐私友好
- 提取元数据完整

**缺点：**
- 需要 Node.js 环境
- 动态页面支持有限
- 首次使用需安装依赖

**适用场景：**
- 高频批量处理
- 静态页面提取
- 离线/内网环境

## 故障排查

### Jina 失败自动降级

当 Jina 不可用时，系统会自动切换到 Defuddle：

```python
client = UrlToMarkdown()  # 自动模式
result = client.fetch("https://example.com")
print(result["_engine_used"])  # 可能输出 "jina" 或 "defuddle"
```

### 常见错误

#### 1. `All engines failed`

两个引擎都失败，检查：
- 网络连接
- URL 是否可访问
- Node.js 是否安装（Defuddle 需要）

#### 2. `Defuddle CLI not found`

Defuddle 未正确安装：

```bash
# 检查 Defuddle 是否存在
ls scripts/url_to_markdown/engines/defuddle-node/dist/cli.js

# 重新安装
cd scripts/url_to_markdown/engines/defuddle-node
npm install
```

#### 3. `Node.js not found`

安装 Node.js：

```bash
# Windows: 下载安装 https://nodejs.org/
# macOS: brew install node
# Linux: apt install nodejs npm
```

## 文件结构

```
union-search-skill/
└── scripts/
    └── url_to_markdown/
        ├── __init__.py              # 模块入口
        ├── url_to_markdown.py       # 双引擎主程序
        ├── README.md                # 本文档
        └── engines/                 # 引擎目录
            ├── __init__.py
            ├── jina_engine.py       # Jina AI 引擎
            ├── defuddle_engine.py   # Defuddle 引擎
            └── defuddle-node/       # Defuddle Node.js 安装
                ├── dist/
                ├── node_modules/
                └── package.json
```

## 性能优化

### 批量处理

```python
from concurrent.futures import ThreadPoolExecutor
from scripts.url_to_markdown import UrlToMarkdown

urls = [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3",
]

client = UrlToMarkdown()

def process_url(url):
    return client.fetch(url)

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(process_url, urls))
```

### 缓存

```python
import hashlib
import json
from pathlib import Path

CACHE_DIR = Path("./url_cache")
CACHE_DIR.mkdir(exist_ok=True)

def get_cached(url, ttl_seconds=3600):
    """获取缓存结果，过期则重新请求"""
    import time
    cache_key = hashlib.md5(url.encode()).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if cache_file.exists():
        data = json.loads(cache_file.read_text())
        if time.time() - data.get("_cached_at", 0) < ttl_seconds:
            return data["result"]

    # Cache miss
    from scripts.url_to_markdown import UrlToMarkdown
    result = UrlToMarkdown().fetch(url)
    cache_file.write_text(json.dumps({
        "_cached_at": time.time(),
        "result": result
    }))
    return result
```

## 最佳实践

1. **默认使用自动模式**：让系统自动选择最佳引擎
2. **批量处理使用 Defuddle**：避免 Jina 速率限制
3. **动态页面优先 Jina**：Defuddle 对 SPA 支持有限
4. **重要内容双重验证**：关键场景可同时用两个引擎验证

## 更新历史

### v2.0.0
- 新增双引擎架构
- 支持自动降级
- 新增 Defuddle 备选引擎
- 优化错误处理

### v1.0.0
- 初始版本（仅 Jina AI）

## License

MIT License
