#!/usr/bin/env python3
"""Reddit Search CLI - Simple command-line interface for YARS."""

import argparse
import json
import sys

from utils import display_results, export_to_csv, export_to_json
from yars import YARS


def create_parser():
    parser = argparse.ArgumentParser(
        description="Reddit Search CLI - Search Reddit posts, users, and subreddits",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--proxy", help="代理地址 (例: http://127.0.0.1:7890)")
    common.add_argument("--timeout", type=int, default=10, help="请求超时时间 (秒)")
    common.add_argument("--output", "-o", help="输出文件路径")
    common.add_argument(
        "--format",
        choices=["json", "csv", "display"],
        default="display",
        help="输出格式 (默认: display)",
    )

    search_parser = subparsers.add_parser("search", parents=[common], help="全站搜索")
    search_parser.add_argument("query", help="搜索关键词")
    search_parser.add_argument("--limit", type=int, default=10, help="结果数量 (默认: 10)")

    subreddit_search_parser = subparsers.add_parser(
        "subreddit-search", parents=[common], help="子版块搜索"
    )
    subreddit_search_parser.add_argument("subreddit", help="子版块名称")
    subreddit_search_parser.add_argument("query", help="搜索关键词")
    subreddit_search_parser.add_argument("--limit", type=int, default=10, help="结果数量")

    post_parser = subparsers.add_parser("post", parents=[common], help="获取帖子详情")
    post_parser.add_argument("permalink", help="帖子链接")

    user_parser = subparsers.add_parser("user", parents=[common], help="获取用户数据")
    user_parser.add_argument("username", help="用户名")
    user_parser.add_argument("--limit", type=int, default=10, help="结果数量")

    subreddit_posts_parser = subparsers.add_parser(
        "subreddit-posts", parents=[common], help="获取子版块帖子"
    )
    subreddit_posts_parser.add_argument("subreddit", help="子版块名称")
    subreddit_posts_parser.add_argument(
        "--category",
        choices=["hot", "top", "new", "rising"],
        default="hot",
        help="分类",
    )
    subreddit_posts_parser.add_argument("--limit", type=int, default=10, help="结果数量")
    subreddit_posts_parser.add_argument(
        "--time-filter",
        choices=["all", "day", "week", "month", "year"],
        default="all",
        help="时间过滤 (仅用于 top)",
    )

    return parser


def execute_command(miner, args):
    command_map = {
        "search": lambda: (
            miner.search_reddit(args.query, limit=args.limit),
            f"Reddit Search: {args.query}",
        ),
        "subreddit-search": lambda: (
            miner.search_subreddit(args.subreddit, args.query, limit=args.limit),
            f"r/{args.subreddit} Search: {args.query}",
        ),
        "post": lambda: (miner.scrape_post_details(args.permalink), "Post Details"),
        "user": lambda: (
            miner.scrape_user_data(args.username, limit=args.limit),
            f"User: u/{args.username}",
        ),
        "subreddit-posts": lambda: (
            miner.fetch_subreddit_posts(
                args.subreddit,
                category=args.category,
                limit=args.limit,
                time_filter=args.time_filter,
            ),
            f"r/{args.subreddit} - {args.category}",
        ),
    }

    if args.command in command_map:
        return command_map[args.command]()
    return None, None


def output_results(results, title, args):
    if args.format == "json":
        if args.output:
            export_to_json(results, args.output)
            print(f"结果已保存到: {args.output}")
        else:
            print(json.dumps(results, indent=2, ensure_ascii=False))
    elif args.format == "csv":
        if not args.output:
            print("错误: CSV 格式需要指定输出文件 (--output)", file=sys.stderr)
            return 1
        export_to_csv(results, args.output)
        print(f"结果已保存到: {args.output}")
    else:
        display_results(results, title)
    return 0


def main():
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    miner = YARS(proxy=args.proxy, timeout=args.timeout)

    try:
        results, title = execute_command(miner, args)
        if results is None:
            parser.print_help()
            return 1

        return output_results(results, title, args)

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
