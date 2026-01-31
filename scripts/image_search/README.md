# Multi-Platform Image Search

多平台图片搜索下载工具 - 支持 17 个图片平台

## 快速开始

### 安装依赖

```bash
pip install pyimagedl
```

### 基本使用

```bash
# 搜索所有平台
python multi_platform_image_search.py "cute cats" --num 50

# 只搜索指定平台
python multi_platform_image_search.py --keyword "sunset" --platforms baidu google pixabay --num 30

# 自定义输出目录
python multi_platform_image_search.py --keyword "flowers" --output ./my_images --num 100

# 列出所有支持的平台
python multi_platform_image_search.py --list-platforms

# 快速测试
python test_image_search.py
```

## 支持的平台（17个）

### 搜索引擎类 (8个)
- **baidu** - 百度图片
- **bing** - 必应图片
- **google** - 谷歌图片
- **i360** - 360 图片
- **sogou** - 搜狗图片
- **yandex** - Yandex 图片
- **yahoo** - Yahoo 图片
- **duckduckgo** - DuckDuckGo 图片

### 高清图库类 (4个)
- **pixabay** - Pixabay（免费高清图库）
- **pexels** - Pexels（免费摄影图库）
- **unsplash** - Unsplash（免费摄影图库）
- **foodiesfeed** - Foodiesfeed（美食图库）

### 动漫图片类 (3个)
- **danbooru** - Danbooru（动漫图片）
- **gelbooru** - Gelbooru（动漫图片）
- **safebooru** - Safebooru（安全动漫图片）

### 其他平台 (2个)
- **huaban** - 花瓣网
- **dimtown** - 次元小镇

## 输出结构

```
image_downloads/
├── baidu_cute_cats_20260201_123456/
│   ├── 00000001.jpg
│   ├── 00000002.png
│   ├── 00000003.webp
│   └── metadata.json          # 图片元数据
├── google_cute_cats_20260201_123457/
│   ├── 00000001.jpg
│   └── metadata.json
├── pixabay_cute_cats_20260201_123458/
│   └── ...
└── responses/
    └── 20260201_123456_image_search_results.json  # 搜索总结
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `keyword` | 搜索关键词（位置参数） | - |
| `--keyword` | 搜索关键词（覆盖位置参数） | - |
| `--platforms` | 指定平台列表 | 所有平台 |
| `--num` | 每平台下载数量 | 50 |
| `--output` | 输出目录 | `image_downloads` |
| `--threads` | 下载线程数 | 5 |
| `--no-metadata` | 不保存元数据 | False |
| `--delay` | 平台间延迟（秒） | 1.0 |
| `--list-platforms` | 列出所有平台 | - |
| `--pretty` | 美化 JSON 输出 | False |
| `--env-file` | 环境变量文件路径 | `.env` |

## 环境变量配置

可以在 `.env` 文件中配置默认值：

```bash
# 图片搜索配置
IMAGE_SEARCH_KEYWORD=cute cats
IMAGE_SEARCH_PLATFORMS=baidu,google,pixabay
IMAGE_SEARCH_NUM=50
IMAGE_SEARCH_OUTPUT=image_downloads
IMAGE_SEARCH_THREADS=5
IMAGE_SEARCH_DELAY=1.0
```

## 使用示例

### 示例 1: 搜索所有平台

```bash
python multi_platform_image_search.py "mountain landscape" --num 100 --output ./landscapes
```

### 示例 2: 只搜索高清图库

```bash
python multi_platform_image_search.py --keyword "coffee" --platforms pixabay pexels unsplash --num 50
```

### 示例 3: 搜索动漫图片

```bash
python multi_platform_image_search.py --keyword "anime girl" --platforms danbooru gelbooru safebooru --num 30
```

### 示例 4: 中文搜索（国内平台）

```bash
python multi_platform_image_search.py --keyword "美食" --platforms baidu sogou i360 huaban --num 50
```

### 示例 5: 使用环境变量

```bash
# 创建 .env 文件
echo "IMAGE_SEARCH_KEYWORD=sunset" > .env
echo "IMAGE_SEARCH_NUM=100" >> .env

# 运行脚本（使用 .env 中的配置）
python multi_platform_image_search.py
```

## 输出格式

### JSON 输出

```json
{
  "saved_to": "responses/20260201_123456_image_search_results.json",
  "summary": {
    "keyword": "cute cats",
    "total_platforms": 17,
    "successful": 15,
    "failed": 2,
    "total_images": 750
  },
  "platforms": [
    {
      "platform": "baidu",
      "keyword": "cute cats",
      "success": true,
      "downloaded": 48,
      "found": 50,
      "output_dir": "./image_downloads/baidu_cute_cats_20260201_123456",
      "metadata_file": "./image_downloads/baidu_cute_cats_20260201_123456/metadata.json"
    }
  ]
}
```

### 元数据格式

每个平台目录下的 `metadata.json`：

```json
{
  "platform": "pixabay",
  "keyword": "cute cats",
  "timestamp": "2026-02-01T12:34:56",
  "total_images": 50,
  "images": [
    {
      "index": 1,
      "identifier": "12345",
      "urls": [
        "https://example.com/image1_full.jpg",
        "https://example.com/image1_large.jpg"
      ],
      "file_path": "/path/to/00000001.jpg",
      "raw_data": {
        "id": 12345,
        "tags": ["cat", "cute", "animal"],
        "likes": 1234,
        "views": 56789
      }
    }
  ]
}
```

## Python API 使用

虽然这是一个命令行工具，但你也可以导入函数使用：

```python
from multi_platform_image_search import search_platform, search_all_platforms

# 单个平台搜索
result = search_platform(
    platform='pixabay',
    keyword='nature',
    num_images=100,
    output_dir='./images',
    num_threads=5,
    save_meta=True
)

# 多平台搜索
results = search_all_platforms(
    keyword='sunset',
    num_images=50,
    platforms=['baidu', 'google', 'pixabay'],
    output_dir='./images',
    num_threads=5,
    save_meta=True,
    delay=1.0
)
```

## 注意事项

1. **依赖安装**: 必须先安装 `pyimagedl` 包
2. **网络要求**: 某些平台可能需要代理访问
3. **API 限制**: 部分平台有请求频率限制
4. **存储空间**: 确保有足够的磁盘空间
5. **平台稳定性**: 某些平台可能暂时不可用

## 常见问题

### Q: 某个平台下载失败怎么办？

A: 检查网络连接，某些平台可能需要代理。查看错误信息了解具体原因。

### Q: 如何提高下载速度？

A: 增加线程数 `--threads 10`，但注意不要过高以免触发反爬虫机制。

### Q: 可以只下载特定类型的图片吗？

A: 目前脚本下载所有找到的图片。可以通过关键词精确控制搜索结果。

### Q: 元数据文件有什么用？

A: 包含图片的原始 URL、标签、点赞数等信息，便于后续分析和溯源。

## 技术特性

- ✅ **完全独立**: 只依赖 `pyimagedl` 包
- ✅ **批量处理**: 支持多平台并发搜索
- ✅ **结构化输出**: 按平台分类，自动生成报告
- ✅ **元数据保存**: 完整保存图片来源信息
- ✅ **错误处理**: 单个平台失败不影响其他平台
- ✅ **进度显示**: 实时显示搜索和下载进度
- ✅ **灵活配置**: 支持命令行和环境变量

## 许可证

基于 imagedl 项目封装，遵循原项目许可证。
