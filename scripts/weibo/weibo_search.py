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
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_str(name, default):
    value = os.getenv(name)
    return default if value is None else value


def _env_file_from_argv(argv):
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
    parser.add_argument("--env-file", default=_env_file_from_argv(sys.argv), help="Env file path")
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
    if args.user_id is None:
        args.user_id = _env_str("WEIBO_USER_ID", "")
    if args.cookie is None:
        args.cookie = _env_str("WEIBO_COOKIE", "")
    if args.filter is None:
        args.filter = _env_int("WEIBO_FILTER", 0)
    if args.since_date is None:
        args.since_date = _env_str("WEIBO_SINCE_DATE", "2025-01-01")
    if args.end_date is None:
        args.end_date = _env_str("WEIBO_END_DATE", "now")
    if args.limit is None:
        args.limit = _env_int("WEIBO_LIMIT", 10)
    if args.sort_by is None:
        args.sort_by = _env_str("WEIBO_SORT_BY", "")
    if args.sort_order is None:
        args.sort_order = _env_str("WEIBO_SORT_ORDER", "desc")
    if args.config_path is None:
        args.config_path = _env_str("WEIBO_CONFIG_PATH", "")
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
    # 如果提供了配置文件路径,直接加载
    if args.config_path:
        config = load_config_from_file(args.config_path)
        # 命令行参数覆盖配置文件
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

    # 否则从命令行参数创建配置
    user_id_list = args.user_id.split(",") if args.user_id else []

    config = {
        "user_id_list": user_id_list,
        "filter": args.filter,
        "since_date": args.since_date,
        "end_date": args.end_date,
        "random_wait_pages": [1, 5],
        "random_wait_seconds": [6, 10],
        "global_wait": [[1000, 3600], [500, 2000]],
        "write_mode": [],  # 不写入文件,只返回数据
        "pic_download": 0,
        "video_download": 0,
        "file_download_timeout": [5, 5, 10],
        "result_dir_name": 0,
        "cookie": args.cookie,
    }

    return config


def sort_weibo_list(weibo_list, sort_by, sort_order):
    """排序微博列表"""
    if not sort_by or sort_by not in ["publish_time", "up_num", "retweet_num", "comment_num"]:
        return weibo_list

    reverse = (sort_order == "desc")

    if sort_by == "publish_time":
        # 时间排序
        return sorted(weibo_list, key=lambda x: x.get(sort_by, ""), reverse=reverse)
    else:
        # 数值排序
        return sorted(weibo_list, key=lambda x: x.get(sort_by, 0), reverse=reverse)


def format_output(user_data, weibo_list, limit):
    """格式化输出"""
    output_lines = []

    # 用户信息
    output_lines.append("=" * 60)
    output_lines.append("用户信息")
    output_lines.append("=" * 60)
    output_lines.append(f"用户ID: {user_data.get('id', 'N/A')}")
    output_lines.append(f"昵称: {user_data.get('nickname', 'N/A')}")
    output_lines.append(f"性别: {user_data.get('gender', 'N/A')}")
    output_lines.append(f"地区: {user_data.get('location', 'N/A')}")
    output_lines.append(f"生日: {user_data.get('birthday', 'N/A')}")
    output_lines.append(f"简介: {user_data.get('description', 'N/A')}")
    output_lines.append(f"认证: {user_data.get('verified_reason', 'N/A')}")
    output_lines.append(f"微博数: {user_data.get('weibo_num', 'N/A')}")
    output_lines.append(f"关注数: {user_data.get('following', 'N/A')}")
    output_lines.append(f"粉丝数: {user_data.get('followers', 'N/A')}")
    output_lines.append("")

    # 微博列表
    output_lines.append("=" * 60)
    output_lines.append(f"微博列表 (共 {len(weibo_list)} 条)")
    output_lines.append("=" * 60)

    for i, weibo in enumerate(weibo_list[:limit], 1):
        output_lines.append(f"\n[{i}] 微博ID: {weibo.get('id', 'N/A')}")

        content = weibo.get('content', 'N/A')
        if len(content) > 200:
            content = content[:200] + "..."
        output_lines.append(f"内容: {content}")

        output_lines.append(f"发布时间: {weibo.get('publish_time', 'N/A')}")
        output_lines.append(f"发布工具: {weibo.get('publish_tool', 'N/A')}")
        output_lines.append(f"发布位置: {weibo.get('publish_place', '无')}")

        # 图片和视频
        pics = weibo.get('original_pictures', '无')
        if pics != '无' and len(pics) > 100:
            pics = pics[:100] + "..."
        output_lines.append(f"图片: {pics}")

        video = weibo.get('video_url', '无')
        if video != '无' and len(video) > 100:
            video = video[:100] + "..."
        output_lines.append(f"视频: {video}")

        # 互动数据
        output_lines.append(
            f"点赞: {weibo.get('up_num', 0)} | "
            f"转发: {weibo.get('retweet_num', 0)} | "
            f"评论: {weibo.get('comment_num', 0)}"
        )
        output_lines.append("-" * 60)

    return "\n".join(output_lines)


def save_raw_response(data, suffix=DEFAULT_SAVE_SUFFIX):
    """保存原始响应到文件"""
    os.makedirs("responses", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"responses/{timestamp}_{suffix}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filename


def main():
    # 解析命令行参数
    args = parse_args()

    # 加载环境变量
    load_env_file(args.env_file)

    # 应用默认值
    args = apply_env_defaults(args)

    # 验证必需参数
    if not args.user_id and not args.config_path:
        print("错误: 必须提供 --user-id 或 --config-path 参数", file=sys.stderr)
        sys.exit(1)

    if not args.cookie and not args.config_path:
        print("错误: 必须提供 --cookie 参数或在环境变量中设置 WEIBO_COOKIE", file=sys.stderr)
        print("提示: 请参考 https://github.com/dataabc/weiboSpider 获取cookie", file=sys.stderr)
        sys.exit(1)

    # 创建配置
    config = create_config(args)

    # 创建 Spider 实例
    print(f"正在初始化微博爬虫...", file=sys.stderr)
    try:
        spider = Spider(config)
    except Exception as e:
        print(f"错误: Spider 初始化失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 收集所有结果
    all_results = []

    # 获取用户列表
    user_id_list = config.get("user_id_list", [])
    if not user_id_list:
        print("错误: 用户ID列表为空", file=sys.stderr)
        sys.exit(1)

    # 遍历每个用户
    for user_id in user_id_list:
        print(f"\n正在获取用户 {user_id} 的数据...", file=sys.stderr)

        try:
            # 设置当前用户
            spider.user_id = user_id

            # 获取用户信息
            spider.get_user_info()

            # 获取微博列表
            spider.get_weibo_info()

            # 提取数据
            user_data = spider.user
            weibo_list = spider.weibo

            # 排序
            if args.sort_by:
                weibo_list = sort_weibo_list(weibo_list, args.sort_by, args.sort_order)

            # 限制数量
            if args.limit:
                weibo_list = weibo_list[:args.limit]

            result = {
                "user_info": user_data,
                "weibo_list": weibo_list,
                "user_id": user_id,
            }

            all_results.append(result)

            print(f"成功获取用户 {user_id} 的 {len(weibo_list)} 条微博", file=sys.stderr)

        except Exception as e:
            print(f"警告: 获取用户 {user_id} 数据失败: {e}", file=sys.stderr)
            continue

    # 保存原始响应
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

    # 输出结果
    if args.json or args.pretty:
        output_data = {
            "results": all_results,
            "total_users": len(all_results),
        }
        if args.pretty:
            print(json.dumps(output_data, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(output_data, ensure_ascii=False))
    else:
        # 文本格式输出
        for result in all_results:
            print(format_output(
                result["user_info"],
                result["weibo_list"],
                args.limit or len(result["weibo_list"])
            ))
            print("\n")


if __name__ == "__main__":
    main()
