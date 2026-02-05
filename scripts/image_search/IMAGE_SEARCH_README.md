# 多平台图片搜索

支持 17 个图片平台的批量搜索和下载工具

## 安装

```bash
pip install pyimagedl
```

## 支持的平台

**搜索引擎**: 百度、Bing、Google、360、搜狗、DuckDuckGo、Yandex、Yahoo

**图库网站**: Pixabay、Pexels、Unsplash、Foodiesfeed

**动漫图片**: Danbooru、Gelbooru、Safebooru

**其他**: 花瓣网、次元小镇

## 使用示例

### 搜索所有平台
```bash
python scripts/image_search/multi_platform_image_search.py "cute cats" --num 50
```

### 搜索指定平台
```bash
python scripts/image_search/multi_platform_image_search.py --keyword "sunset" --platforms baidu google pixabay --num 30
```

### 自定义输出目录
```bash
python scripts/image_search/multi_platform_image_search.py --keyword "flowers" --output ./my_images --num 100
```

### 列出所有平台
```bash
python scripts/image_search/multi_platform_image_search.py --list-platforms
```

## 主要参数

- `--keyword, -k`: 搜索关键词（必需）
- `--platforms, -p`: 指定平台列表（默认所有平台）
- `--num, -n`: 每个平台的图片数量（默认 50）
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
├── search_summary.json
└── search_summary.md
```

每个平台目录包含下载的图片和元数据文件。
