# Defuddle 引擎

Defuddle 是 URL to Markdown 模块的备选引擎，在 Jina AI 失败时自动使用。

## 定位

- **首选引擎**: Jina AI Reader API
- **备选引擎**: Defuddle

Defuddle 作为本地运行的引擎，无速率限制，适合高频批量处理。

## 目录结构

```
engines/
├── defuddle/
│   ├── defuddle_cli.py    # Python CLI（独立使用）
│   └── README.md          # 本文档
├── defuddle-node/         # Node.js 运行时
│   ├── dist/
│   ├── node_modules/
│   └── package.json
├── defuddle_engine.py     # 引擎适配器
└── jina_engine.py         # Jina 引擎适配器
```

## 使用方法

### 通过主模块（推荐）

```python
from scripts.url_to_markdown import UrlToMarkdown

# 自动模式 - 优先 Jina，失败时 Defuddle
client = UrlToMarkdown()
result = client.fetch("https://example.com")

# 仅使用 Defuddle
client = UrlToMarkdown(prefer_engine="defuddle", enable_fallback=False)
result = client.fetch("https://example.com")
```

### 直接使用 Defuddle 引擎

```python
from scripts.url_to_markdown.engines.defuddle_engine import DefuddleEngine

client = DefuddleEngine()
result = client.fetch(url="https://example.com")
```

### 独立 CLI

```bash
python scripts/url_to_markdown/engines/defuddle/defuddle_cli.py https://example.com
```

## 安装说明

Defuddle 需要 Node.js 环境：

```bash
# 检查 Node.js
node --version

# 安装依赖
cd scripts/url_to_markdown/engines/defuddle-node
npm install
```

## 更新 Defuddle

```bash
# 从 defuddle-main 复制最新版本
cp -r /path/to/defuddle-main/dist/* scripts/url_to_markdown/engines/defuddle-node/dist/

# 验证
node scripts/url_to_markdown/engines/defuddle-node/dist/cli.js --version
```

## 参考

- [Defuddle GitHub](https://github.com/kepano/defuddle)
- [主 README](../README.md)
