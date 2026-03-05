#!/usr/bin/env python3
"""
Bilibili 搜索工具 - 使用 TikHub API
支持视频搜索、用户搜索等

使用方法:
    python bilibili_tikhub_search.py "Python教程" --limit 10
    python bilibili_tikhub_search.py "Python教程" --json --pretty
"""

import argparse
import http.client
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_env():
    """加载 .env 文件中的环境变量"""
    # 从项目根目录加载 .env
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key and key not in os.environ:
                    os.environ[key] = value


def get_tikhub_token():
    """获取 TikHub Token"""
    token = os.environ.get("TIKHUB_TOKEN")
    if not token:
        print("错误: 未找到 TIKHUB_TOKEN 环境变量", file=sys.stderr)
        print("请在 .env 文件中设置 TIKHUB_TOKEN", file=sys.stderr)
        sys.exit(1)
    return token


def get_base_url():
    """根据网络状况选择 API 域名"""
    import socket
    try:
        socket.gethostbyname("api.tikhub.io")
        return "api.tikhub.io"
    except socket.gaierror:
        return "api.tikhub.dev"


def search_bilibili(keyword: str, limit: int = 10, order: str = "totalrank") -> list:
    """
    搜索 Bilibili 视频

    Args:
        keyword: 搜索关键词
        limit: 返回结果数量
        order: 排序方式 (totalrank, click, pubdate, danmaku)

    Returns:
        视频列表
    """
    token = get_tikhub_token()
    base_url = get_base_url()

    encoded_keyword = quote(keyword)

    conn = http.client.HTTPSConnection(base_url)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"/api/v1/bilibili/web/fetch_general_search?keyword={encoded_keyword}&order={order}&page=1&page_size={limit}"
    conn.request("GET", url, "", headers)

    res = conn.getresponse()
    if res.status != 200:
        raise Exception(f"API 请求失败: HTTP {res.status}")

    data = res.read()
    response = json.loads(data.decode("utf-8"))

    if response.get("code") != 200:
        raise Exception(f"API 错误: {response.get('message', 'Unknown error')}")

    videos = response.get("data", {}).get("data", {}).get("result", [])

    results = []
    for v in videos:
        results.append({
            "bvid": v.get("bvid"),
            "title": v.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
            "author": v.get("author"),
            "mid": v.get("mid"),
            "aid": v.get("aid"),
            "arcurl": v.get("arcurl"),
            "description": v.get("description"),
            "pic": v.get("pic"),
            "play": v.get("play"),
            "duration": v.get("duration"),
            "favorites": v.get("favorites"),
            "like": v.get("like"),
            "pubdate": v.get("pubdate"),
            "tag": v.get("tag"),
        })

    return results


def format_json(results: list, pretty: bool = False) -> str:
    """格式化 JSON 输出"""
    if pretty:
        return json.dumps(results, ensure_ascii=False, indent=2)
    return json.dumps(results, ensure_ascii=False)


def format_markdown(results: list, keyword: str) -> str:
    """格式化 Markdown 输出"""
    lines = [f"# Bilibili 搜索结果: {keyword}\n"]
    lines.append(f"共找到 {len(results)} 个视频\n\n")

    for i, v in enumerate(results, 1):
        lines.append(f"## [{i}] {v.get('title', 'N/A')}\n")
        lines.append(f"- **BV号**: {v.get('bvid')}\n")
        lines.append(f"- **作者**: {v.get('author')}\n")
        lines.append(f"- **播放**: {v.get('play', 0):,}\n")
        lines.append(f"- **时长**: {v.get('duration', 'N/A')}\n")
        lines.append(f"- **链接**: {v.get('arcurl')}\n")
        lines.append(f"- **标签**: {v.get('tag', 'N/A')}\n")
        lines.append("\n")

    return "".join(lines)


def format_text(results: list) -> str:
    """格式化纯文本输出"""
    lines = [f"Bilibili 搜索结果 (共 {len(results)} 个)\n"]
    lines.append("=" * 60 + "\n\n")

    for i, v in enumerate(results, 1):
        title = v.get('title', 'N/A')[:50]
        lines.append(f"[{i}] {title}")
        lines.append(f"    作者: {v.get('author')} | 播放: {v.get('play', 0):,} | 时长: {v.get('duration', 'N/A')}")
        lines.append(f"    链接: {v.get('arcurl')}")
        lines.append("")

    return "\n".join(lines)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Bilibili 搜索工具 (TikHub API)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python bilibili_tikhub_search.py "Python教程"
  python bilibili_tikhub_search.py "Python教程" --limit 5
  python bilibili_tikhub_search.py "Python教程" --json
  python bilibili_tikhub_search.py "Python教程" -o results.json
        """
    )

    parser.add_argument("keyword", help="搜索关键词")
    parser.add_argument("--limit", "-l", type=int, default=10, help="返回结果数量 (默认: 10)")
    parser.add_argument("--order", "-o", default="totalrank",
                        choices=["totalrank", "click", "pubdate", "danmaku"],
                        help="排序方式 (默认: totalrank)")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--pretty", action="store_true", help="美化 JSON 输出")
    parser.add_argument("--output", "-f", help="保存结果到文件")

    args = parser.parse_args()

    # 加载环境变量
    load_env()

    try:
        results = search_bilibili(args.keyword, limit=args.limit, order=args.order)

        if args.json:
            output = format_json(results, pretty=args.pretty)
        else:
            output = format_text(results)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"结果已保存到: {args.output}")
        else:
            print(output)

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
