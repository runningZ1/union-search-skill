#!/usr/bin/env python3
"""
微博搜索脚本 - 集成版
直接使用 weiboSpider 项目的核心功能
"""
import argparse
import json
import os
import sys
from datetime import datetime

# 添加 weiboSpider 项目路径到 sys.path
WEIBO_SPIDER_PATH = r"D:\Programs\weiboSpider"
if WEIBO_SPIDER_PATH not in sys.path:
    sys.path.insert(0, WEIBO_SPIDER_PATH)

try:
    from weibo_spider.spider import Spider
    from weibo_spider import config_util
except ImportError as e:
    print(f"错误: 无法导入 weibo_spider 模块", file=sys.stderr)
    print(f"请确保 weiboSpider 项目位于: {WEIBO_SPIDER_PATH}", file=sys.stderr)
    print(f"详细错误: {e}", file=sys.stderr)
    sys.exit(1)


DEFAULT_SAVE_SUFFIX = "weibo_search"


def load_env_file(path):
    """加载环境变量文件"""
    if not path or not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()

            if key and key not in os.environ:
                os.environ[key] = value


def get_env_int(name, default):
    """获取整数类型的环境变量"""
    value = os.getenv(name)
    if not value:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def get_env_str(name, default):
    """获取字符串类型的环境变量"""
    value = os.getenv(name)
    return value if value is not None else default


def get_env_file_from_argv(argv):
    """从命令行参数中提取环境变量文件路径"""
    for i, arg in enumerate(argv):
        if arg == "--env-file" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--env-file="):
            return arg.split("=", 1)[1]
    return ".env"


def parse_args():
    examples = (
        "Examples:\n"
        "  python weibo_search.py --user-id 1669879400\n"
        "  python weibo_search.py --user-id 1669879400 --limit 20 --filter 1\n"
        "  python weibo_search.py --user-id 1669879400,1223178222 --since-date 2025-01-01\n"
        "  python weibo_search.py --config-path config.json\n"
    )
    parser = argparse.ArgumentParser(
        description="Weibo search client (integrated with weiboSpider)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=examples,
    )
    parser.add_argument("--env-file", default=get_env_file_from_argv(sys.argv), help="Env file path")
    parser.add_argument("--user-id", help="Weibo user ID(s), comma-separated for multiple users")
    parser.add_argument("--cookie", help="Weibo cookie for authentication")
    parser.add_argument("--filter", type=int, choices=[0, 1], help="0=all weibo, 1=original only (default: 0)")
    parser.add_argument("--since-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD or 'now')")
    parser.add_argument("--limit", type=int, help="Max weibo items per user (default: 10)")
    parser.add_argument("--sort-by", help="Sort by field: publish_time/up_num/retweet_num/comment_num")
    parser.add_argument("--sort-order", choices=["asc", "desc"], help="Sort order (asc/desc)")
    parser.add_argument("--config-path", help="Path to weiboSpider config.json file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--save-raw", action="store_true", help="Save raw response to responses/ directory")
    return parser.parse_args()


def apply_env_defaults(args):
    """应用环境变量默认值"""
    args.user_id = args.user_id or get_env_str("WEIBO_USER_ID", "")
    args.cookie = args.cookie or get_env_str("WEIBO_COOKIE", "")
    args.filter = args.filter if args.filter is not None else get_env_int("WEIBO_FILTER", 0)
    args.since_date = args.since_date or get_env_str("WEIBO_SINCE_DATE", "2025-01-01")
    args.end_date = args.end_date or get_env_str("WEIBO_END_DATE", "now")
    args.limit = args.limit or get_env_int("WEIBO_LIMIT", 10)
    args.sort_by = args.sort_by or get_env_str("WEIBO_SORT_BY", "")
    args.sort_order = args.sort_order or get_env_str("WEIBO_SORT_ORDER", "desc")
    args.config_path = args.config_path or get_env_str("WEIBO_CONFIG_PATH", "")
    return args


def load_config_from_file(config_path):
    """从配置文件加载配置"""
    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_config(args):
    """创建 Spider 配置"""
    if args.config_path:
        config = load_config_from_file(args.config_path)

        if args.user_id:
            config["user_id_list"] = args.user_id.split(",")
        if args.cookie:
            config["cookie"] = args.cookie
        if args.filter is not None:
            config["filter"] = args.filter
        if args.since_date:
            config["since_date"] = args.since_date
        if args.end_date:
            config["end_date"] = args.end_date

        return config

    user_id_list = args.user_id.split(",") if args.user_id else []

    return {
        "user_id_list": user_id_list,
        "filter": args.filter,
        "since_date": args.since_date,
        "end_date": args.end_date,
        "random_wait_pages": [1, 5],
        "random_wait_seconds": [6, 10],
        "global_wait": [[1000, 3600], [500, 2000]],
        "write_mode": [],
        "pic_download": 0,
        "video_download": 0,
        "file_download_timeout": [5, 5, 10],
        "result_dir_name": 0,
        "cookie": args.cookie,
    }


def sort_weibo_list(weibo_list, sort_by, sort_order):
    """排序微博列表"""
    valid_fields = ["publish_time", "up_num", "retweet_num", "comment_num"]
    if not sort_by or sort_by not in valid_fields:
        return weibo_list

    reverse = (sort_order == "desc")
    key_func = lambda x: x.get(sort_by, "" if sort_by == "publish_time" else 0)
    return sorted(weibo_list, key=key_func, reverse=reverse)


def format_output(user_data, weibo_list, limit):
    """格式化输出"""
    lines = [
        "=" * 60,
        "用户信息",
        "=" * 60,
        f"用户ID: {user_data.get('id', 'N/A')}",
        f"昵称: {user_data.get('nickname', 'N/A')}",
        f"性别: {user_data.get('gender', 'N/A')}",
        f"地区: {user_data.get('location', 'N/A')}",
        f"生日: {user_data.get('birthday', 'N/A')}",
        f"简介: {user_data.get('description', 'N/A')}",
        f"认证: {user_data.get('verified_reason', 'N/A')}",
        f"微博数: {user_data.get('weibo_num', 'N/A')}",
        f"关注数: {user_data.get('following', 'N/A')}",
        f"粉丝数: {user_data.get('followers', 'N/A')}",
        "",
        "=" * 60,
        f"微博列表 (共 {len(weibo_list)} 条)",
        "=" * 60,
    ]

    for i, weibo in enumerate(weibo_list[:limit], 1):
        content = weibo.get('content', 'N/A')
        if len(content) > 200:
            content = content[:200] + "..."

        pics = weibo.get('original_pictures', '无')
        if pics != '无' and len(pics) > 100:
            pics = pics[:100] + "..."

        video = weibo.get('video_url', '无')
        if video != '无' and len(video) > 100:
            video = video[:100] + "..."

        lines.extend([
            f"\n[{i}] 微博ID: {weibo.get('id', 'N/A')}",
            f"内容: {content}",
            f"发布时间: {weibo.get('publish_time', 'N/A')}",
            f"发布工具: {weibo.get('publish_tool', 'N/A')}",
            f"发布位置: {weibo.get('publish_place', '无')}",
            f"图片: {pics}",
            f"视频: {video}",
            f"点赞: {weibo.get('up_num', 0)} | 转发: {weibo.get('retweet_num', 0)} | 评论: {weibo.get('comment_num', 0)}",
            "-" * 60,
        ])

    return "\n".join(lines)


def save_raw_response(data, suffix=DEFAULT_SAVE_SUFFIX):
    """保存原始响应到文件"""
    os.makedirs("responses", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"responses/{timestamp}_{suffix}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filename


def main():
    args = parse_args()
    load_env_file(args.env_file)
    args = apply_env_defaults(args)

    if not args.user_id and not args.config_path:
        print("错误: 必须提供 --user-id 或 --config-path 参数", file=sys.stderr)
        sys.exit(1)

    if not args.cookie and not args.config_path:
        print("错误: 必须提供 --cookie 参数或在环境变量中设置 WEIBO_COOKIE", file=sys.stderr)
        print("提示: 请参考 https://github.com/dataabc/weiboSpider 获取cookie", file=sys.stderr)
        sys.exit(1)

    config = create_config(args)

    print(f"正在初始化微博爬虫...", file=sys.stderr)
    try:
        spider = Spider(config)
    except Exception as e:
        print(f"错误: Spider 初始化失败: {e}", file=sys.stderr)
        sys.exit(1)

    all_results = []
    user_id_list = config.get("user_id_list", [])

    if not user_id_list:
        print("错误: 用户ID列表为空", file=sys.stderr)
        sys.exit(1)

    for user_id in user_id_list:
        print(f"\n正在获取用户 {user_id} 的数据...", file=sys.stderr)

        try:
            spider.user_id = user_id
            spider.get_user_info()
            spider.get_weibo_info()

            user_data = spider.user
            weibo_list = spider.weibo

            if args.sort_by:
                weibo_list = sort_weibo_list(weibo_list, args.sort_by, args.sort_order)

            if args.limit:
                weibo_list = weibo_list[:args.limit]

            all_results.append({
                "user_info": user_data,
                "weibo_list": weibo_list,
                "user_id": user_id,
            })

            print(f"成功获取用户 {user_id} 的 {len(weibo_list)} 条微博", file=sys.stderr)

        except Exception as e:
            print(f"警告: 获取用户 {user_id} 数据失败: {e}", file=sys.stderr)
            continue

    if args.save_raw:
        raw_data = {
            "results": all_results,
            "query_params": {
                "user_id_list": user_id_list,
                "filter": config.get("filter"),
                "since_date": config.get("since_date"),
                "end_date": config.get("end_date"),
                "limit": args.limit,
                "sort_by": args.sort_by,
                "sort_order": args.sort_order,
            },
            "timestamp": datetime.now().isoformat(),
        }
        filename = save_raw_response(raw_data)
        print(f"\n原始响应已保存到: {filename}", file=sys.stderr)

    if args.json or args.pretty:
        output_data = {
            "results": all_results,
            "total_users": len(all_results),
        }
        indent = 2 if args.pretty else None
        print(json.dumps(output_data, ensure_ascii=False, indent=indent))
    else:
        for result in all_results:
            print(format_output(
                result["user_info"],
                result["weibo_list"],
                args.limit or len(result["weibo_list"])
            ))
            print("\n")


if __name__ == "__main__":
    main()
