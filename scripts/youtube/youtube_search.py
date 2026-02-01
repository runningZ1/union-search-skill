#!/usr/bin/env python3
"""
YouTube 视频搜索工具 (基于 YouTube Data API v3)
支持搜索视频、获取详细信息、互动数据、评论区等
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import re


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


def parse_duration(duration: str) -> str:
    """
    解析 ISO 8601 时长格式 (PT1H2M10S) 为可读格式

    Args:
        duration: ISO 8601 格式的时长字符串

    Returns:
        格式化的时长字符串 (例: "1:02:10")
    """
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return duration

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def make_api_request(url: str, params: Dict) -> Dict:
    """
    发送 API 请求

    Args:
        url: API 端点 URL
        params: 请求参数

    Returns:
        API 响应的 JSON 数据
    """
    query_string = urlencode(params)
    full_url = f"{url}?{query_string}"

    try:
        req = Request(full_url)
        req.add_header('User-Agent', 'Mozilla/5.0')

        with urlopen(req, timeout=30) as response:
            data = response.read()
            return json.loads(data.decode('utf-8'))
    except HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_body)
            error_msg = error_data.get('error', {}).get('message', str(e))
        except:
            error_msg = str(e)
        raise Exception(f"API 请求失败: {error_msg}")
    except URLError as e:
        raise Exception(f"网络错误: {e.reason}")
    except Exception as e:
        raise Exception(f"请求失败: {str(e)}")


def search_videos(
    api_key: str,
    keyword: str,
    limit: int = 10,
    order: str = "relevance",
    region_code: str = "US",
    language: str = "zh-CN",
) -> List[str]:
    """
    搜索 YouTube 视频

    Args:
        api_key: YouTube Data API 密钥
        keyword: 搜索关键词
        limit: 返回结果数量
        order: 排序方式 (relevance, date, rating, viewCount, title)
        region_code: 地区代码
        language: 语言代码

    Returns:
        视频 ID 列表
    """
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": api_key,
        "q": keyword,
        "part": "snippet",
        "type": "video",
        "maxResults": min(limit, 50),  # API 限制最多 50
        "order": order,
        "regionCode": region_code,
        "relevanceLanguage": language,
    }

    result = make_api_request(url, params)

    video_ids = []
    for item in result.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        if video_id:
            video_ids.append(video_id)

    return video_ids


def get_video_details(
    api_key: str,
    video_ids: List[str],
    include_comments: bool = False,
    max_comments: int = 10,
) -> List[Dict]:
    """
    获取视频详细信息

    Args:
        api_key: YouTube Data API 密钥
        video_ids: 视频 ID 列表
        include_comments: 是否包含评论
        max_comments: 每个视频的最大评论数

    Returns:
        视频详细信息列表
    """
    if not video_ids:
        return []

    # 获取视频详细信息
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "key": api_key,
        "id": ",".join(video_ids),
        "part": "snippet,statistics,contentDetails",
    }

    result = make_api_request(url, params)

    videos = []
    for idx, item in enumerate(result.get("items", []), 1):
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})

        video_data = {
            "rank": idx,
            "video_id": item.get("id", ""),
            "title": snippet.get("title", ""),
            "channel_title": snippet.get("channelTitle", ""),
            "channel_id": snippet.get("channelId", ""),
            "published_at": snippet.get("publishedAt", ""),
            "description": snippet.get("description", ""),
            "thumbnails": snippet.get("thumbnails", {}),
            "tags": snippet.get("tags", []),
            "category_id": snippet.get("categoryId", ""),
            "duration": parse_duration(content_details.get("duration", "")),
            "duration_raw": content_details.get("duration", ""),
            "definition": content_details.get("definition", ""),
            "caption": content_details.get("caption", ""),
            "statistics": {
                "view_count": int(statistics.get("viewCount", 0)),
                "like_count": int(statistics.get("likeCount", 0)),
                "comment_count": int(statistics.get("commentCount", 0)),
            },
            "url": f"https://www.youtube.com/watch?v={item.get('id', '')}",
        }

        # 获取评论
        if include_comments:
            try:
                comments = get_video_comments(api_key, item.get("id", ""), max_comments)
                video_data["comments"] = comments
            except Exception as e:
                video_data["comments_error"] = str(e)

        videos.append(video_data)

    return videos


def get_video_comments(
    api_key: str,
    video_id: str,
    max_results: int = 10,
) -> List[Dict]:
    """
    获取视频评论

    Args:
        api_key: YouTube Data API 密钥
        video_id: 视频 ID
        max_results: 最大评论数

    Returns:
        评论列表
    """
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "key": api_key,
        "videoId": video_id,
        "part": "snippet",
        "maxResults": min(max_results, 100),
        "order": "relevance",  # 按相关性排序（热门评论）
    }

    try:
        result = make_api_request(url, params)
    except Exception as e:
        # 评论可能被禁用
        if "disabled comments" in str(e).lower():
            return []
        raise

    comments = []
    for item in result.get("items", []):
        top_comment = item.get("snippet", {}).get("topLevelComment", {})
        snippet = top_comment.get("snippet", {})

        comment_data = {
            "author": snippet.get("authorDisplayName", ""),
            "author_channel_id": snippet.get("authorChannelId", {}).get("value", ""),
            "text": snippet.get("textDisplay", ""),
            "like_count": snippet.get("likeCount", 0),
            "published_at": snippet.get("publishedAt", ""),
            "updated_at": snippet.get("updatedAt", ""),
        }
        comments.append(comment_data)

    return comments


def format_text_output(results: List[Dict], keyword: str, include_comments: bool):
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
        print(f"视频ID: {result['video_id']}")
        print(f"频道: {result['channel_title']}")
        print(f"频道ID: {result['channel_id']}")
        print(f"发布时间: {result['published_at']}")
        print(f"时长: {result['duration']}")
        print(f"视频链接: {result['url']}")

        print(f"\n【互动数据】")
        stats = result['statistics']
        print(f"▶️  播放量: {stats['view_count']:,}")
        print(f"💖 点赞数: {stats['like_count']:,}")
        print(f"💭 评论数: {stats['comment_count']:,}")

        print(f"\n【视频信息】")
        print(f"分类ID: {result['category_id']}")
        print(f"清晰度: {result['definition'].upper()}")
        print(f"字幕: {'有' if result['caption'] == 'true' else '无'}")

        if result.get('tags'):
            print(f"\n【视频标签】")
            print(f"标签: {', '.join(result['tags'][:10])}")

        if result.get('description'):
            print(f"\n【视频简介】")
            desc = result['description'][:200] + '...' if len(result['description']) > 200 else result['description']
            print(f"{desc}")

        if include_comments and 'comments' in result:
            print(f"\n【热门评论】")
            for i, comment in enumerate(result['comments'][:5], 1):
                print(f"\n评论 #{i}")
                print(f"作者: {comment['author']}")
                print(f"点赞: {comment['like_count']}")
                print(f"内容: {comment['text'][:150]}")

        if 'comments_error' in result:
            print(f"\n⚠️  评论获取失败: {result['comments_error']}")

        print()


def format_markdown_output(results: List[Dict], keyword: str, include_comments: bool) -> str:
    """格式化 Markdown 输出"""
    md = f"# YouTube 视频搜索结果\n\n"
    md += f"**搜索关键词**: {keyword}\n\n"
    md += f"**结果数量**: {len(results)}\n\n"
    md += f"---\n\n"

    for result in results:
        md += f"## 视频 #{result['rank']}: {result['title']}\n\n"

        # 缩略图
        thumbnails = result.get('thumbnails', {})
        if 'high' in thumbnails:
            md += f"![{result['title']}]({thumbnails['high']['url']})\n\n"

        md += f"### 基础信息\n\n"
        md += f"| 项目 | 内容 |\n"
        md += f"|------|------|\n"
        md += f"| **标题** | {result['title']} |\n"
        md += f"| **视频ID** | {result['video_id']} |\n"
        md += f"| **频道** | {result['channel_title']} |\n"
        md += f"| **频道ID** | {result['channel_id']} |\n"
        md += f"| **发布时间** | {result['published_at']} |\n"
        md += f"| **时长** | {result['duration']} |\n"
        md += f"| **视频链接** | [点击观看]({result['url']}) |\n\n"

        stats = result['statistics']
        md += f"### 互动数据\n\n"
        md += f"| 指标 | 数值 |\n"
        md += f"|------|------|\n"
        md += f"| ▶️ **播放量** | {stats['view_count']:,} |\n"
        md += f"| 💖 **点赞数** | {stats['like_count']:,} |\n"
        md += f"| 💭 **评论数** | {stats['comment_count']:,} |\n\n"

        if result.get('description'):
            md += f"### 视频简介\n\n{result['description']}\n\n"

        if result.get('tags'):
            md += f"### 标签\n\n{', '.join(result['tags'])}\n\n"

        if include_comments and 'comments' in result:
            md += f"### 热门评论\n\n"
            for i, comment in enumerate(result['comments'], 1):
                md += f"**{i}. {comment['author']}** (👍 {comment['like_count']})\n\n"
                md += f"{comment['text']}\n\n"

        md += f"---\n\n"

    return md


def parse_args():
    parser = argparse.ArgumentParser(
        description="YouTube 视频搜索工具 (基于 YouTube Data API v3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python youtube_search.py "Python tutorial" --limit 5
  python youtube_search.py "机器学习" --order viewCount --limit 10
  python youtube_search.py "AI" --json --pretty
  python youtube_search.py "编程" --markdown -o results.md
  python youtube_search.py "教程" --include-comments --max-comments 5

排序方式:
  relevance  - 相关性 (默认)
  date       - 发布日期
  rating     - 评分
  viewCount  - 播放量
  title      - 标题
"""
    )

    parser.add_argument("keyword", nargs="?", help="搜索关键词")
    parser.add_argument("--keyword", dest="keyword_opt", help="搜索关键词 (覆盖位置参数)")
    parser.add_argument("--api-key", help="YouTube Data API 密钥")
    parser.add_argument("--limit", type=int, default=10, help="返回结果数量 (默认: 10, 最大: 50)")
    parser.add_argument("--order", choices=["relevance", "date", "rating", "viewCount", "title"],
                       default="relevance", help="排序方式 (默认: relevance)")
    parser.add_argument("--region", default="US", help="地区代码 (默认: US)")
    parser.add_argument("--language", default="zh-CN", help="语言代码 (默认: zh-CN)")
    parser.add_argument("--include-comments", action="store_true", help="包含评论区内容")
    parser.add_argument("--max-comments", type=int, default=10, help="每个视频的最大评论数 (默认: 10)")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--pretty", action="store_true", help="格式化 JSON 输出")
    parser.add_argument("--markdown", action="store_true", help="Markdown 格式输出")
    parser.add_argument("-o", "--output", help="保存输出到文件")
    parser.add_argument("--save-raw", action="store_true", help="保存原始响应到 responses/ 目录")
    parser.add_argument("--env-file", default=".env", help="环境变量文件路径")

    return parser.parse_args()


def main():
    args = parse_args()

    # 加载环境变量
    env_file = Path(__file__).parent.parent.parent / args.env_file
    load_env_file(str(env_file))

    # 确定 API 密钥
    api_key = args.api_key or os.getenv("YOUTUBE_API_KEY", "")
    if not api_key:
        print("错误: 缺少 YouTube API 密钥", file=sys.stderr)
        print("使用方式: python youtube_search.py \"关键词\" --api-key YOUR_API_KEY", file=sys.stderr)
        print("或在 .env 文件中设置 YOUTUBE_API_KEY", file=sys.stderr)
        return 1

    # 确定关键词
    keyword = args.keyword_opt if args.keyword_opt else args.keyword
    if not keyword:
        keyword = os.getenv("YOUTUBE_KEYWORD", "")

    if not keyword:
        print("错误: 缺少搜索关键词", file=sys.stderr)
        print("使用方式: python youtube_search.py \"关键词\"", file=sys.stderr)
        return 1

    # 执行搜索
    try:
        # 搜索视频
        video_ids = search_videos(
            api_key=api_key,
            keyword=keyword,
            limit=args.limit,
            order=args.order,
            region_code=args.region,
            language=args.language,
        )

        if not video_ids:
            print(f"未找到关键词 '{keyword}' 的相关视频", file=sys.stderr)
            return 1

        # 获取详细信息
        results = get_video_details(
            api_key=api_key,
            video_ids=video_ids,
            include_comments=args.include_comments,
            max_comments=args.max_comments,
        )

        if not results:
            print(f"获取视频详细信息失败", file=sys.stderr)
            return 1

        # 保存原始响应
        if args.save_raw:
            responses_dir = Path(__file__).parent / "responses"
            responses_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_file = responses_dir / f"youtube_search_{timestamp}.json"
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"原始响应已保存: {raw_file}", file=sys.stderr)

        # 输出结果
        output_content = None

        if args.json:
            output_content = json.dumps(results, ensure_ascii=False, indent=2 if args.pretty else None)
        elif args.markdown:
            output_content = format_markdown_output(results, keyword, args.include_comments)
        else:
            format_text_output(results, keyword, args.include_comments)

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
    sys.exit(main())
