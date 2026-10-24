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
│   ├── node_modules/       # npm ci 安装，包含 defuddle/dist/cli.js
│   ├── package-lock.json
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

Defuddle 需要 Node.js 18+ 和 npm。在仓库根目录安装正式 npm 包：

```bash
node --version
npm --prefix scripts/url_to_markdown/engines/defuddle-node ci
node scripts/url_to_markdown/engines/defuddle-node/node_modules/defuddle/dist/cli.js --version
```

`package.json` 固定 `defuddle@0.10.0` 和 `jsdom@24.1.3`，`package-lock.json` 固定传递依赖。新克隆使用 `npm ci` 即可恢复运行时。三个 Python 入口均调用此子目录中的 `node_modules/defuddle/dist/cli.js`。

## 更新 Defuddle

在 `engines/defuddle-node/package.json` 中修改精确版本后，运行以下命令更新锁文件并验证实际提取结果：

```bash
npm --prefix scripts/url_to_markdown/engines/defuddle-node install --package-lock-only
npm --prefix scripts/url_to_markdown/engines/defuddle-node ci
python scripts/url_to_markdown/engines/defuddle/defuddle_cli.py https://example.com --json
```

## 参考

- [Defuddle GitHub](https://github.com/kepano/defuddle)
- [网页正文提取模块](../../README.md)
