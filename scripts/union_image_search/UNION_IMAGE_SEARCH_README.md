# Union Image Search - 多平台图片搜索

支持 18 个图片平台的批量搜索和下载工具 (新增火山引擎)

## 安装

```bash
pip install pyimagedl
```

**注意**: 火山引擎平台需要配置 API Key:

```bash
# 在 .env 文件中添加
VOLCENGINE_API_KEY=your_api_key_here
```

## 支持的平台

**搜索引擎**: 百度、Bing、Google、360、搜狗、Yandex、Yahoo

**图库网站**: Pixabay、Pexels、Unsplash、Foodiesfeed

**动漫图片**: Danbooru、Gelbooru、Safebooru

**其他**: 花瓣网、火山引擎 (API-based)

## 使用示例

### 搜索所有平台
```bash
python scripts/union_image_search/multi_platform_image_search.py "cute cats"
```

### 搜索指定平台
```bash
python scripts/union_image_search/multi_platform_image_search.py --keyword "sunset" --platforms baidu google pixabay --num 20

# 使用火山引擎 (需要 API Key)
python scripts/union_image_search/multi_platform_image_search.py --keyword "风景" --platforms volcengine --num 5
```

### 自定义输出目录
```bash
python scripts/union_image_search/multi_platform_image_search.py --keyword "flowers" --output ./my_images --num 50
```

### 列出所有平台
```bash
python scripts/union_image_search/multi_platform_image_search.py --list-platforms
```

## 主要参数

- `--keyword, -k`: 搜索关键词（必需）
- `--platforms, -p`: 指定平台列表（默认所有平台）
  - 可选平台: baidu, bing, google, i360, pixabay, yandex, sogou, yahoo, unsplash, gelbooru, safebooru, danbooru, pexels, huaban, foodiesfeed, volcengine
- `--num, -n`: 每个平台的图片数量（默认 10，火山引擎最多 5）
- `--output, -o`: 输出目录（默认 `image_downloads`）
- `--threads, -t`: 下载线程数（默认 5）
- `--no-metadata`: 不保存元数据
- `--delay`: 平台间延迟秒数（默认 1.0）

## 输出结构

```
image_downloads/
├── baidu_cute_cats_20260130_123456/
│   ├── 00000001.jpg
│   └── metadata.json
├── google_cute_cats_20260130_123457/
│   └── ...
├── volcengine_cute_cats_20260130_123458/
│   ├── 00000001.jpg
│   └── metadata.json
├── search_summary.json
└── search_summary.md
```

每个平台目录包含下载的图片和元数据文件。

## 平台特性

### 火山引擎 (Volcengine)

- **类型**: API-based (需要 API Key)
- **限制**: 最多 5 张图片/请求
- **特性**:
  - 支持尺寸过滤 (width_min, width_max, height_min, height_max)
  - 支持形状过滤 (横长方形、竖长方形、方形)
  - 高质量图片源
- **配置**: 需要在 `.env` 文件中设置 `VOLCENGINE_API_KEY`
- **获取 API Key**: https://console.volcengine.com/ask-echo/api-key
