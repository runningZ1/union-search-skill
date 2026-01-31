#!/usr/bin/env python3
"""
Multi-Platform Image Search and Download Script
完全独立的全平台图片搜索下载脚本

支持 17 个图片平台的批量搜索和下载
依赖: pip install pyimagedl
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

# 检查依赖
try:
    from imagedl import imagedl
except ImportError:
    print("错误：未安装 pyimagedl 包", file=sys.stderr)
    print("请运行：pip install pyimagedl", file=sys.stderr)
    sys.exit(1)

# 支持的所有平台配置
SUPPORTED_PLATFORMS = {
    'baidu': 'BaiduImageClient',
    'bing': 'BingImageClient',
    'google': 'GoogleImageClient',
    'i360': 'I360ImageClient',
    'pixabay': 'PixabayImageClient',
    'yandex': 'YandexImageClient',
    'sogou': 'SogouImageClient',
    'yahoo': 'YahooImageClient',
    'unsplash': 'UnsplashImageClient',
    'gelbooru': 'GelbooruImageClient',
    'safebooru': 'SafebooruImageClient',
    'danbooru': 'DanbooruImageClient',
    'pexels': 'PexelsImageClient',
    'dimtown': 'DimTownImageClient',
    'huaban': 'HuabanImageClient',
    'foodiesfeed': 'FoodiesfeedImageClient',
    'duckduckgo': 'DuckduckgoImageClient',
}

DEFAULT_SAVE_SUFFIX = "image_search_results"


def load_env_file(path):
    """加载环境变量文件"""
    if not path or not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value


def _env_int(name, default):
    """获取整数环境变量"""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_str(name, default):
    """获取字符串环境变量"""
    value = os.getenv(name)
    return default if value is None else value


def _env_file_from_argv(argv):
    """从命令行参数获取环境变量文件路径"""
    for i, arg in enumerate(argv):
        if arg == "--env-file" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--env-file="):
            return arg.split("=", 1)[1]
    return ".env"


def parse_args():
    """解析命令行参数"""
    examples = (
        "Examples:\n"
        "  python multi_platform_image_search.py \"cute cats\" --num 50\n"
        "  python multi_platform_image_search.py --keyword \"sunset\" --platforms baidu google pixabay\n"
        "  python multi_platform_image_search.py --keyword \"flowers\" --output ./my_images --num 100\n"
        "  python multi_platform_image_search.py --list-platforms\n"
    )
    parser = argparse.ArgumentParser(
        description="Multi-platform image search and download tool",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=examples,
    )
    parser.add_argument("--env-file", default=_env_file_from_argv(sys.argv), help="Env file path")
    parser.add_argument("keyword", nargs="?", help="Search keyword (positional)")
    parser.add_argument("--keyword", dest="keyword_opt", help="Search keyword (overrides positional)")
    parser.add_argument("--platforms", nargs="+", choices=list(SUPPORTED_PLATFORMS.keys()),
                       help="Specify platform list (default: all platforms)")
    parser.add_argument("--num", type=int, help="Images per platform (default: 50)")
    parser.add_argument("--output", help="Output directory (default: image_downloads)")
    parser.add_argument("--threads", type=int, help="Download threads (default: 5)")
    parser.add_argument("--no-metadata", action="store_true", help="Don't save metadata")
    parser.add_argument("--delay", type=float, help="Delay between platforms in seconds (default: 1.0)")
    parser.add_argument("--list-platforms", action="store_true", help="List all supported platforms")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser.parse_args()


def apply_env_defaults(args):
    """应用环境变量默认值"""
    keyword = args.keyword_opt if args.keyword_opt is not None else args.keyword
    if keyword is None:
        keyword = _env_str("IMAGE_SEARCH_KEYWORD", "")
    args.keyword = keyword

    if args.platforms is None:
        platforms_str = _env_str("IMAGE_SEARCH_PLATFORMS", "")
        args.platforms = platforms_str.split(",") if platforms_str else None

    if args.num is None:
        args.num = _env_int("IMAGE_SEARCH_NUM", 50)

    if args.output is None:
        args.output = _env_str("IMAGE_SEARCH_OUTPUT", "image_downloads")

    if args.threads is None:
        args.threads = _env_int("IMAGE_SEARCH_THREADS", 5)

    if args.delay is None:
        args.delay = float(_env_str("IMAGE_SEARCH_DELAY", "1.0"))

    return args


def count_downloaded_images(directory):
    """统计目录中下载的图片数量"""
    if not os.path.exists(directory):
        return 0

    count = 0
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff')

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(image_extensions):
                count += 1

    return count


def save_metadata(platform_dir, platform, keyword, image_infos):
    """保存元数据到 JSON 文件"""
    metadata = {
        'platform': platform,
        'keyword': keyword,
        'timestamp': datetime.now().isoformat(),
        'total_images': len(image_infos),
        'images': []
    }

    # 提取关键信息
    for idx, info in enumerate(image_infos, 1):
        image_meta = {
            'index': idx,
            'identifier': info.get('identifier', ''),
            'urls': info.get('candidate_urls', []),
            'file_path': info.get('file_path', ''),
            'raw_data': info.get('raw_data', {})
        }
        metadata['images'].append(image_meta)

    # 保存到文件
    metadata_file = os.path.join(platform_dir, 'metadata.json')
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return metadata_file


def search_platform(platform, keyword, num_images, output_dir, num_threads, save_meta):
    """在单个平台搜索图片"""
    if platform not in SUPPORTED_PLATFORMS:
        return {
            'platform': platform,
            'keyword': keyword,
            'success': False,
            'error': f'不支持的平台: {platform}',
            'downloaded': 0,
            'metadata': []
        }

    platform_client_name = SUPPORTED_PLATFORMS[platform]

    # 创建平台专属目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keyword = keyword.replace(' ', '_').replace('/', '_')
    platform_dir = os.path.join(output_dir, f"{platform}_{safe_keyword}_{timestamp}")

    print(f"\n{'='*70}")
    print(f"平台: {platform.upper()} | 关键词: '{keyword}' | 目标: {num_images} 张")
    print(f"{'='*70}")

    try:
        # 创建客户端
        client = imagedl.ImageClient(
            image_source=platform_client_name,
            init_image_client_cfg={'work_dir': platform_dir},
            search_limits=num_images,
            num_threadings=num_threads
        )

        # 搜索图片
        print(f"[1/2] 正在搜索...")
        image_infos = client.search(
            keyword,
            search_limits_overrides=num_images,
            num_threadings_overrides=num_threads
        )

        if not image_infos:
            print(f"✗ 未找到图片")
            return {
                'platform': platform,
                'keyword': keyword,
                'success': False,
                'error': '未找到图片',
                'downloaded': 0,
                'metadata': [],
                'output_dir': platform_dir
            }

        print(f"✓ 找到 {len(image_infos)} 张图片")

        # 下载图片
        print(f"[2/2] 正在下载...")
        client.download(
            image_infos=image_infos,
            num_threadings_overrides=num_threads
        )

        # 统计下载结果
        downloaded_count = count_downloaded_images(platform_dir)

        # 保存元数据
        metadata_file = None
        if save_meta and image_infos:
            metadata_file = save_metadata(platform_dir, platform, keyword, image_infos)

        print(f"✓ 成功下载 {downloaded_count} 张图片")
        print(f"✓ 保存位置: {platform_dir}")

        return {
            'platform': platform,
            'keyword': keyword,
            'success': True,
            'downloaded': downloaded_count,
            'found': len(image_infos),
            'metadata': image_infos,
            'output_dir': platform_dir,
            'metadata_file': metadata_file
        }

    except Exception as e:
        error_msg = str(e)
        print(f"✗ 错误: {error_msg}")
        return {
            'platform': platform,
            'keyword': keyword,
            'success': False,
            'error': error_msg,
            'downloaded': 0,
            'metadata': [],
            'output_dir': platform_dir
        }


def search_all_platforms(keyword, num_images, platforms, output_dir, num_threads, save_meta, delay):
    """在所有平台搜索图片"""
    if platforms is None:
        platforms = list(SUPPORTED_PLATFORMS.keys())

    print(f"\n{'='*70}")
    print(f"多平台图片搜索")
    print(f"{'='*70}")
    print(f"关键词: {keyword}")
    print(f"平台数: {len(platforms)}")
    print(f"每平台: {num_images} 张")
    print(f"输出目录: {output_dir}")
    print(f"{'='*70}\n")

    results = {
        'keyword': keyword,
        'total_platforms': len(platforms),
        'timestamp': datetime.now().isoformat(),
        'platforms': []
    }

    for i, platform in enumerate(platforms, 1):
        print(f"\n[{i}/{len(platforms)}] 处理平台: {platform.upper()}")

        result = search_platform(platform, keyword, num_images, output_dir, num_threads, save_meta)
        results['platforms'].append(result)

        # 平台间延迟
        if i < len(platforms):
            time.sleep(delay)

    return results


def print_summary(results):
    """打印搜索总结"""
    successful = [p for p in results['platforms'] if p['success']]
    failed = [p for p in results['platforms'] if not p['success']]
    total_images = sum(p['downloaded'] for p in successful)

    print(f"\n{'='*70}")
    print(f"搜索完成！")
    print(f"{'='*70}\n")

    print(f"✅ 成功的平台 ({len(successful)}/{results['total_platforms']}):")
    for p in successful:
        print(f"  - {p['platform']:15s}: {p['downloaded']:3d} 张 (找到 {p.get('found', 0)} 张)")

    if failed:
        print(f"\n❌ 失败的平台 ({len(failed)}/{results['total_platforms']}):")
        for p in failed:
            error = p['error'][:60]
            print(f"  - {p['platform']:15s}: {error}")

    print(f"\n📊 总计:")
    print(f"  - 成功平台: {len(successful)}")
    print(f"  - 失败平台: {len(failed)}")
    print(f"  - 总下载图片: {total_images} 张")
    if results['total_platforms'] > 0:
        print(f"  - 成功率: {len(successful)*100//results['total_platforms']}%")

    print(f"\n{'='*70}\n")


def save_summary(results, base_dir):
    """保存搜索总结报告"""
    save_dir = os.path.join(base_dir, "responses")
    os.makedirs(save_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{DEFAULT_SAVE_SUFFIX}.json"
    save_path = os.path.join(save_dir, filename)

    # 简化结果（移除大量元数据）
    simplified_results = {
        'keyword': results['keyword'],
        'total_platforms': results['total_platforms'],
        'timestamp': results['timestamp'],
        'platforms': []
    }

    for platform_result in results['platforms']:
        simplified_results['platforms'].append({
            'platform': platform_result['platform'],
            'keyword': platform_result['keyword'],
            'success': platform_result['success'],
            'downloaded': platform_result['downloaded'],
            'found': platform_result.get('found', 0),
            'error': platform_result.get('error', ''),
            'output_dir': platform_result['output_dir'],
            'metadata_file': platform_result.get('metadata_file', '')
        })

    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(simplified_results, f, ensure_ascii=False, indent=2)

    return save_path


def main():
    """主函数"""
    env_file = _env_file_from_argv(sys.argv)
    load_env_file(env_file)
    args = apply_env_defaults(parse_args())

    # 列出平台
    if args.list_platforms:
        print("\n支持的平台列表:")
        print("="*50)
        for short_name, full_name in SUPPORTED_PLATFORMS.items():
            print(f"  {short_name:15s} -> {full_name}")
        print("="*50)
        print(f"总计: {len(SUPPORTED_PLATFORMS)} 个平台\n")
        return 0

    # 检查必需参数
    if not args.keyword:
        print("错误：必须指定搜索关键词", file=sys.stderr)
        print("使用 --keyword 参数或位置参数提供关键词", file=sys.stderr)
        return 2

    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)

    # 执行搜索
    results = search_all_platforms(
        keyword=args.keyword,
        num_images=args.num,
        platforms=args.platforms,
        output_dir=args.output,
        num_threads=args.threads,
        save_meta=not args.no_metadata,
        delay=args.delay
    )

    # 打印总结
    print_summary(results)

    # 保存总结报告
    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_path = save_summary(results, base_dir)

    # 准备输出
    output = {
        'saved_to': save_path,
        'summary': {
            'keyword': results['keyword'],
            'total_platforms': results['total_platforms'],
            'successful': len([p for p in results['platforms'] if p['success']]),
            'failed': len([p for p in results['platforms'] if not p['success']]),
            'total_images': sum(p['downloaded'] for p in results['platforms'] if p['success'])
        },
        'platforms': results['platforms']
    }

    # 输出 JSON
    if args.pretty:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(output, ensure_ascii=False))

    print(f"\n✓ 搜索报告已保存: {save_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
