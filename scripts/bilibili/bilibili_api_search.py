#!/usr/bin/env python3
"""
Bilibili 视频高级搜索工具 (基于 bilibili-api 库)
支持按播放量排序、获取详细视频信息、互动数据、UP主信息等
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from bilibili_api import search, video
except ImportError:
    print("错误: 未安装 bilibili-api 库", file=sys.stderr)
    print("请运行: pip install bilibili-api-python aiohttp", file=sys.stderr)
    sys.exit(1)


def load_env_file(path: str):
    """加载环境变量文件"""
    if not path or not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value


async def search_videos(
    keyword: str,
    limit: int = 10,
    order_type: str = "totalrank",
    get_details: bool = True,
    save_raw: bool = False,
) -> List[Dict]:
    """
    搜索 Bilibili 视频

    Args:
        keyword: 搜索关键词
        limit: 返回结果数量
        order_type: 排序方式 (totalrank=综合, click=播放量, pubdate=发布时间, dm=弹幕, stow=收藏)
        get_details: 是否获取详细信息
        save_raw: 是否保存原始响应
    """
    # 排序类型映射
    order_map = {
        "totalrank": search.OrderVideo.TOTALRANK,
        "click": search.OrderVideo.CLICK,
        "pubdate": search.OrderVideo.PUBDATE,
        "dm": search.OrderVideo.DM,
        "stow": search.OrderVideo.STOW,
    }

    order = order_map.get(order_type, search.OrderVideo.TOTALRANK)

    # 执行搜索
    search_result = await search.search_by_type(
        keyword=keyword,
        search_type=search.SearchObjectType.VIDEO,
        order_type=order,
        page=1
    )

    results = search_result.get('result', [])

    if not results:
        return []

    # 保存原始响应
    if save_raw:
        responses_dir = Path(__file__).parent / "responses"
        responses_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_file = responses_dir / f"bilibili_search_{timestamp}.json"
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(search_result, f, ensure_ascii=False, indent=2)
        print(f"原始响应已保存: {raw_file}", file=sys.stderr)

    # 按播放量排序
    sorted_results = sorted(
        results,
        key=lambda x: int(x.get('play', 0)),
        reverse=True
    )[:limit]

    # 获取详细信息
    detailed_results = []
    for idx, item in enumerate(sorted_results, 1):
        result_data = {
            'rank': idx,
            'bvid': item.get('bvid', ''),
            'title': item.get('title', '').replace('<em class="keyword">', '').replace('</em>', ''),
            'author': item.get('author', ''),
            'mid': item.get('mid', ''),
            'duration': item.get('duration', ''),
            'pubdate': item.get('pubdate', ''),
            'play': item.get('play', 0),
            'video_review': item.get('video_review', 0),
            'like': item.get('like', 0),
            'favorites': item.get('favorites', 0),
            'url': f"https://www.bilibili.com/video/{item.get('bvid', '')}",
        }

        # 获取详细信息
        if get_details:
            try:
                v = video.Video(bvid=item.get('bvid', ''))
                detail_info = await v.get_info()

                stat = detail_info.get('stat', {})
                owner = detail_info.get('owner', {})

                result_data.update({
                    'aid': detail_info.get('aid', ''),
                    'tname': detail_info.get('tname', ''),
                    'copyright': '原创' if detail_info.get('copyright') == 1 else '转载',
                    'desc': detail_info.get('desc', ''),
                    'pic': detail_info.get('pic', ''),
                    'stat': {
                        'view': stat.get('view', 0),
                        'danmaku': stat.get('danmaku', 0),
                        'like': stat.get('like', 0),
                        'coin': stat.get('coin', 0),
                        'favorite': stat.get('favorite', 0),
                        'share': stat.get('share', 0),
                        'reply': stat.get('reply', 0),
                    },
                    'owner': {
                        'name': owner.get('name', ''),
                        'mid': owner.get('mid', ''),
                        'face': owner.get('face', ''),
                    }
                })

                # 获取视频标签
                try:
                    tags = await v.get_tags()
                    result_data['tags'] = [tag.get('tag_name', '') for tag in tags[:10]]
                except:
                    result_data['tags'] = []

                await asyncio.sleep(0.3)  # 避免请求过快

            except Exception as e:
                result_data['error'] = str(e)

        detailed_results.append(result_data)

    return detailed_results


def format_text_output(results: List[Dict], keyword: str):
    """格式化文本输出"""
    print(f"\n{'='*80}")
    print(f"🔍 搜索关键词: {keyword}")
    print(f"📊 结果数量: {len(results)}")
    print(f"{'='*80}\n")

    for result in results:
        print(f"{'='*80}")
        print(f"📹 视频 #{result['rank']}")
        print(f"{'='*80}")
        print(f"\n【基础信息】")
        print(f"标题: {result['title']}")
        print(f"BVID: {result['bvid']}")
        print(f"作者: {result['author']}")
        print(f"UP主ID: {result['mid']}")
        print(f"时长: {result['duration']}")
        print(f"发布时间: {result['pubdate']}")
        print(f"视频链接: {result['url']}")

        if 'stat' in result:
            print(f"\n【互动数据】")
            stat = result['stat']
            print(f"▶️  播放量: {stat['view']:,}")
            print(f"💬 弹幕数: {stat['danmaku']:,}")
            print(f"💖 点赞数: {stat['like']:,}")
            print(f"🪙 投币数: {stat['coin']:,}")
            print(f"⭐ 收藏数: {stat['favorite']:,}")
            print(f"🔄 转发数: {stat['share']:,}")
            print(f"💭 评论数: {stat['reply']:,}")

        if 'tname' in result:
            print(f"\n【视频信息】")
            print(f"AV号: av{result.get('aid', 'N/A')}")
            print(f"分区: {result['tname']}")
            print(f"版权: {result['copyright']}")
            if result.get('desc'):
                desc = result['desc'][:100] + '...' if len(result['desc']) > 100 else result['desc']
                print(f"简介: {desc}")

        if 'tags' in result and result['tags']:
            print(f"\n【视频标签】")
            print(f"标签: {', '.join(result['tags'])}")

        if 'error' in result:
            print(f"\n❌ 获取详细信息失败: {result['error']}")

        print()


def format_markdown_output(results: List[Dict], keyword: str) -> str:
    """格式化 Markdown 输出"""
    md = f"# Bilibili 视频搜索结果\n\n"
    md += f"**搜索关键词**: {keyword}\n\n"
    md += f"**结果数量**: {len(results)}\n\n"
    md += f"---\n\n"

    for result in results:
        md += f"## 视频 #{result['rank']}: {result['title']}\n\n"

        md += f"### 基础信息\n\n"
        md += f"| 项目 | 内容 |\n"
        md += f"|------|------|\n"
        md += f"| **标题** | {result['title']} |\n"
        md += f"| **BVID** | {result['bvid']} |\n"
        md += f"| **作者** | {result['author']} |\n"
        md += f"| **UP主ID** | {result['mid']} |\n"
        md += f"| **时长** | {result['duration']} |\n"
        md += f"| **发布时间** | {result['pubdate']} |\n"
        md += f"| **视频链接** | [点击观看]({result['url']}) |\n\n"

        if 'stat' in result:
            stat = result['stat']
            md += f"### 互动数据\n\n"
            md += f"| 指标 | 数值 |\n"
            md += f"|------|------|\n"
            md += f"| ▶️ **播放量** | {stat['view']:,} |\n"
            md += f"| 💬 **弹幕数** | {stat['danmaku']:,} |\n"
            md += f"| 💖 **点赞数** | {stat['like']:,} |\n"
            md += f"| 🪙 **投币数** | {stat['coin']:,} |\n"
            md += f"| ⭐ **收藏数** | {stat['favorite']:,} |\n"
            md += f"| 🔄 **转发数** | {stat['share']:,} |\n"
            md += f"| 💭 **评论数** | {stat['reply']:,} |\n\n"

        if 'desc' in result and result['desc']:
            md += f"### 视频简介\n\n{result['desc']}\n\n"

        if 'tags' in result and result['tags']:
            md += f"### 标签\n\n{', '.join(result['tags'])}\n\n"

        md += f"---\n\n"

    return md


def parse_args():
    parser = argparse.ArgumentParser(
        description="Bilibili 视频高级搜索工具 (基于 bilibili-api 库)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python bilibili_api_search.py "Python教程" --limit 5
  python bilibili_api_search.py "原神" --order click --limit 10
  python bilibili_api_search.py "机器学习" --json --pretty
  python bilibili_api_search.py "编程" --markdown -o results.md
  python bilibili_api_search.py "AI" --no-details --save-raw

排序方式:
  totalrank  - 综合排序 (默认)
  click      - 播放量
  pubdate    - 发布时间
  dm         - 弹幕数
  stow       - 收藏数
"""
    )

    parser.add_argument("keyword", nargs="?", help="搜索关键词")
    parser.add_argument("--keyword", dest="keyword_opt", help="搜索关键词 (覆盖位置参数)")
    parser.add_argument("--limit", type=int, default=10, help="返回结果数量 (默认: 10)")
    parser.add_argument("--order", choices=["totalrank", "click", "pubdate", "dm", "stow"],
                       default="totalrank", help="排序方式 (默认: totalrank)")
    parser.add_argument("--no-details", action="store_true", help="不获取详细信息")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--pretty", action="store_true", help="格式化 JSON 输出")
    parser.add_argument("--markdown", action="store_true", help="Markdown 格式输出")
    parser.add_argument("-o", "--output", help="保存输出到文件")
    parser.add_argument("--save-raw", action="store_true", help="保存原始响应到 responses/ 目录")
    parser.add_argument("--env-file", default=".env", help="环境变量文件路径")

    return parser.parse_args()


async def main():
    args = parse_args()

    # 加载环境变量
    env_file = Path(__file__).parent.parent.parent / args.env_file
    load_env_file(str(env_file))

    # 确定关键词
    keyword = args.keyword_opt if args.keyword_opt else args.keyword
    if not keyword:
        keyword = os.getenv("BILIBILI_API_KEYWORD", "")

    if not keyword:
        print("错误: 缺少搜索关键词", file=sys.stderr)
        print("使用方式: python bilibili_api_search.py \"关键词\"", file=sys.stderr)
        return 1

    # 执行搜索
    try:
        results = await search_videos(
            keyword=keyword,
            limit=args.limit,
            order_type=args.order,
            get_details=not args.no_details,
            save_raw=args.save_raw,
        )

        if not results:
            print(f"未找到关键词 '{keyword}' 的相关视频", file=sys.stderr)
            return 1

        # 输出结果
        output_content = None

        if args.json:
            output_content = json.dumps(results, ensure_ascii=False, indent=2 if args.pretty else None)
        elif args.markdown:
            output_content = format_markdown_output(results, keyword)
        else:
            format_text_output(results, keyword)

        # 保存到文件
        if args.output and output_content:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_content)
            print(f"\n结果已保存到: {args.output}", file=sys.stderr)
        elif output_content:
            print(output_content)

        return 0

    except Exception as e:
        print(f"搜索失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
