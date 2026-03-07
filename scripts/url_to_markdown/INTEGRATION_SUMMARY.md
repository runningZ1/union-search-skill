# Defuddle 集成总结

## 架构说明

本次集成将 Defuddle 作为 Jina AI 的**备选引擎**，实现了双引擎自动降级架构：

```
用户请求
    ↓
尝试 Jina AI API（首选）
    ↓
成功 → 返回结果 ✓
    ↓
失败 → 自动切换到 Defuddle（备选）
    ↓
返回结果 ✓ 或报错 ✗
```

## 目录结构调整

```
union-search-skill/
└── scripts/
    └── url_to_markdown/          # URL 转 Markdown 主模块
        ├── __init__.py
        ├── url_to_markdown.py    # 双引擎主程序
        ├── README.md             # 主文档
        └── engines/              # 引擎目录
            ├── __init__.py
            ├── jina_engine.py    # Jina AI 引擎
            ├── defuddle_engine.py # Defuddle 引擎
            ├── defuckle/         # Defuddle Python 包装器
            │   ├── defuddle_cli.py
            │   └── README.md
            └── defuddle-node/    # Defuddle Node.js 运行时
                ├── dist/
                ├── node_modules/
                └── package.json
```

## 核心改动

### 1. 新增文件

| 文件 | 说明 |
|------|------|
| `url_to_markdown/engines/__init__.py` | 引擎模块入口 |
| `url_to_markdown/engines/jina_engine.py` | Jina 引擎类 |
| `url_to_markdown/engines/defuddle_engine.py` | Defuddle 引擎类 |
| `url_to_markdown/engines/defuddle/defuddle_cli.py` | Defuddle CLI |
| `url_to_markdown/engines/defuddle/README.md` | Defuddle 文档 |

### 2. 修改文件

| 文件 | 修改内容 |
|------|---------|
| `url_to_markdown/__init__.py` | 更新文档说明双引擎架构 |
| `url_to_markdown/url_to_markdown.py` | 重写为双引擎版本 |
| `url_to_markdown/README.md` | 更新为双引擎文档 |
| `cli/adapters.py` | 更新 `run_defuddle` 导入路径 |
| `cli/main.py` | 更新 `handle_defuddle` 导入路径 |
| `union_search/union_search.py` | 添加 defuddle 到 PLATFORM_MODULES |
| `cli/registry.py` | 添加 defuddle 配置 |
| `cli/output.py` | 添加 defuddle 专用输出格式 |

### 3. 移动的文件

- `defuddle-node/` → `url_to_markdown/engines/defuddle-node/`
- `scripts/defuddle/` → `url_to_markdown/engines/defuddle/`

## 使用方式

### Python API

```python
from scripts.url_to_markdown import UrlToMarkdown, fetch_url_as_markdown

# 默认自动模式（优先 Jina，失败时 Defuddle）
result = fetch_url_as_markdown("https://example.com")

# 指定引擎
client = UrlToMarkdown(prefer_engine="jina")  # 仅 Jina
client = UrlToMarkdown(prefer_engine="defuddle")  # 仅 Defuddle
client = UrlToMarkdown(prefer_engine="auto")  # 自动降级
```

### CLI

```bash
# 使用双引擎（自动模式）
python scripts/url_to_markdown/url_to_markdown.py https://example.com

# 指定引擎
python scripts/url_to_markdown/url_to_markdown.py https://example.com --prefer-engine jina
python scripts/url_to_markdown/url_to_markdown.py https://example.com --prefer-engine defuddle

# CLI defuddle 命令
python scripts/cli/main.py defuddle https://example.com
```

## 引擎对比

| 特性 | Jina AI（首选） | Defuddle（备选） |
|------|----------------|-----------------|
| 类型 | API | 本地 |
| 速率限制 | 20 RPM（免费） | 无限制 |
| 依赖 | 无 | Node.js |
| 动态页面 | 支持好 | 有限支持 |
| 元数据 | 完整 | 完整 |
| 隐私 | API 传输 | 本地处理 |

## 自动降级场景

1. **Jina API 不可达**（网络问题）
2. **Jina 速率限制**（429 错误）
3. **Jina 解析失败**（页面结构特殊）
4. **手动指定**（`prefer_engine="defuddle"`）

## 验收测试

```bash
# 测试 Jina 引擎
python scripts/url_to_markdown/url_to_markdown.py https://example.com --prefer-engine jina
# 输出：[使用引擎：jina]

# 测试 Defuddle 引擎
python scripts/url_to_markdown/url_to_markdown.py https://example.com --prefer-engine defuddle
# 输出：[使用引擎：defuddle]

# 测试自动降级（默认）
python scripts/url_to_markdown/url_to_markdown.py https://example.com
# 输出：[使用引擎：jina]（Jina 成功）
# 或 [使用引擎：defuddle]（Jina 失败时）

# 测试 CLI defuddle 命令
python scripts/cli/main.py defuddle https://example.com --format markdown
```

## 注意事项

1. **Node.js 必需**：Defuddle 引擎需要 Node.js 18+
2. **路径变更**：Defuddle 现在位于 `url_to_markdown/engines/defuddle-node/`
3. **导入更新**：使用 `from url_to_markdown.engines.defuddle_engine import DefuddleEngine`

## 后续优化

1. **缓存层**：添加本地缓存减少重复请求
2. **智能选择**：根据 URL 域名自动选择最佳引擎
3. **并行请求**：同时请求两个引擎，返回最快的结果
4. **监控统计**：记录引擎成功率和性能数据

## 版本历史

- **v2.0.0** - 双引擎架构，自动降级
- **v1.0.0** - 初始版本（仅 Jina）
