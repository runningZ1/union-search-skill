# Brave 搜索模块

使用 Brave Search 进行网络搜索。

## 特点

- 无需 API 密钥
- 隐私保护
- 支持分页
- 支持时间过滤
- 支持安全搜索设置

## 使用方法

### 基本搜索

```bash
python scripts/brave/brave_search.py "machine learning"
```

### 高级选项

```bash
# 指定页码和结果数
python scripts/brave/brave_search.py "blockchain" -p 2 -m 15

# 时间过滤
python scripts/brave/brave_search.py "tech news" -t w  # 最近一周

# 国家设置
python scripts/brave/brave_search.py "local news" -c us

# 安全搜索
python scripts/brave/brave_search.py "content" -s strict

# JSON 输出
python scripts/brave/brave_search.py "web3" --json --pretty

# 使用代理
python scripts/brave/brave_search.py "search query" --proxy http://127.0.0.1:7890
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-p, --page` | 页码 | 1 |
| `-m, --max-results` | 最大结果数 | 10 |
| `-c, --country` | 国家代码 | us |
| `-s, --safesearch` | 安全搜索 (off/moderate/strict) | moderate |
| `-t, --timelimit` | 时间限制 (d/w/m/y) | 无 |
| `--proxy` | 代理地址 | 无 |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON | False |

## 环境变量

```bash
# .env 文件（可选）
BRAVE_PROXY=http://127.0.0.1:7890
```

## 国家代码

- `us` - 美国
- `uk` - 英国
- `ca` - 加拿大
- `au` - 澳大利亚
- `de` - 德国
- `fr` - 法国
- `jp` - 日本
- `cn` - 中国

## 时间限制

- `d` - 最近一天
- `w` - 最近一周
- `m` - 最近一月
- `y` - 最近一年

## 依赖

```bash
pip install requests lxml python-dotenv
```
