#!/usr/bin/env python3
"""
Twitter 搜索结果筛选器
从完整的 API 响应中提取核心信息,生成精简版本
"""
import json
import sys
from typing import Dict, List, Any, Optional


def extract_core_media(media_data: Dict[str, Any]) -> Dict[str, Any]:
    """提取媒体核心信息"""
    if not media_data:
        return {}

    core_media = {}
    for media_type, items in media_data.items():
        if items and isinstance(items, list):
            core_media[media_type] = []
            for item in items:
                media_info = {
                    "media_url_https": item.get("media_url_https"),
                    "id": item.get("id") or item.get("id_str"),
                    "type": item.get("type", media_type),
                }

                # 提取尺寸信息(保留原始尺寸)
                if "sizes" in item and "original_info" in item:
                    orig = item.get("original_info", {})
                    media_info["width"] = orig.get("width")
                    media_info["height"] = orig.get("height")
                elif "sizes" in item:
                    # 保留 large 尺寸
                    sizes = item.get("sizes", {})
                    if "large" in sizes:
                        media_info["width"] = sizes["large"].get("w")
                        media_info["height"] = sizes["large"].get("h")

                core_media[media_type].append(media_info)

    return core_media


def extract_entities(entities_data: Dict[str, Any]) -> Dict[str, Any]:
    """提取实体核心信息"""
    if not entities_data:
        return {}

    core_entities = {}

    # 提取话题标签
    if entities_data.get("hashtags"):
        core_entities["hashtags"] = [
            tag.get("text") for tag in entities_data["hashtags"]
        ]

    # 提取 URL
    if entities_data.get("urls"):
        core_entities["urls"] = [
            {
                "display_url": url.get("display_url"),
                "expanded_url": url.get("expanded_url"),
            }
            for url in entities_data["urls"]
        ]

    # 提及的用户
    if entities_data.get("user_mentions"):
        core_entities["user_mentions"] = [
            {
                "screen_name": mention.get("screen_name"),
                "name": mention.get("name"),
            }
            for mention in entities_data["user_mentions"]
        ]

    return core_entities


def extract_tweet_url(screen_name: str, tweet_id: str) -> str:
    """生成推文链接"""
    return f"https://x.com/{screen_name}/status/{tweet_id}"


def extract_core_tweet(tweet: Dict[str, Any]) -> Dict[str, Any]:
    """提取单条推文的核心信息"""
    screen_name = tweet.get("screen_name", "")
    tweet_id = tweet.get("tweet_id", "")

    core_tweet = {
        # 基本信息
        "tweet_id": tweet_id,
        "url": extract_tweet_url(screen_name, tweet_id),
        "type": tweet.get("type"),

        # 内容
        "text": tweet.get("text"),
        "lang": tweet.get("lang"),
        "created_at": tweet.get("created_at"),

        # 作者核心信息
        "author": {
            "screen_name": screen_name,
            "name": tweet.get("user_info", {}).get("name"),
            "verified": tweet.get("user_info", {}).get("verified", False),
            "followers_count": tweet.get("user_info", {}).get("followers_count"),
            "description": tweet.get("user_info", {}).get("description"),
        },

        # 互动数据
        "metrics": {
            "favorites": tweet.get("favorites", 0),
            "retweets": tweet.get("retweets", 0),
            "replies": tweet.get("replies", 0),
            "quotes": tweet.get("quotes", 0),
            "bookmarks": tweet.get("bookmarks", 0),
            "views": tweet.get("views", "0"),
        },

        # 媒体信息
        "media": extract_core_media(tweet.get("media")),

        # 实体信息
        "entities": extract_entities(tweet.get("entities")),

        # 对话ID(用于获取回复)
        "conversation_id": tweet.get("conversation_id"),
    }

    return core_tweet


def extract_core_response(full_response: Dict[str, Any]) -> Dict[str, Any]:
    """提取完整响应的核心信息"""
    # 检查响应是否成功
    if full_response.get("code") != 200:
        return {
            "success": False,
            "error": full_response.get("detail", full_response.get("message")),
            "original_response": full_response,
        }

    # 提取核心元数据
    core_response = {
        "success": True,
        "metadata": {
            "keyword": full_response.get("params", {}).get("keyword"),
            "search_type": full_response.get("params", {}).get("search_type"),
            "request_id": full_response.get("request_id"),
            "search_time": full_response.get("time"),
            "cache_url": full_response.get("cache_url"),
        },

        # 统计信息
        "stats": {
            "total_tweets": len(full_response.get("data", {}).get("timeline", [])),
        },

        # 提取推文列表
        "tweets": [],
    }

    # 提取每条推文的核心信息
    timeline = full_response.get("data", {}).get("timeline", [])
    for tweet in timeline:
        if tweet.get("type") == "tweet":
            core_tweet = extract_core_tweet(tweet)
            core_response["tweets"].append(core_tweet)

    return core_response


def filter_response(input_file: str, output_file: Optional[str] = None, pretty: bool = True) -> Dict[str, Any]:
    """
    筛选 Twitter API 响应文件

    Args:
        input_file: 输入文件路径(完整响应)
        output_file: 输出文件路径(筛选后的响应),如果为None则自动生成
        pretty: 是否格式化 JSON

    Returns:
        筛选后的响应数据
    """
    # 读取完整响应
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            full_response = json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败 - {e}", file=sys.stderr)
        sys.exit(1)

    # 提取核心信息
    core_response = extract_core_response(full_response)

    # 生成输出文件名
    if output_file is None:
        if "_full" not in input_file:
            base_name = input_file.replace(".json", "")
            output_file = f"{base_name}_core.json"
        else:
            output_file = input_file.replace("_full.json", "_core.json")

    # 保存筛选后的响应
    with open(output_file, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(core_response, f, indent=2, ensure_ascii=False)
        else:
            json.dump(core_response, f, ensure_ascii=False)

    print(f"✅ 筛选完成!")
    print(f"   输入文件: {input_file}")
    print(f"   输出文件: {output_file}")
    print(f"   推文数量: {core_response.get('stats', {}).get('total_tweets', 0)}")

    return core_response


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="筛选 Twitter API 响应,提取核心信息",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("input_file", help="输入文件路径(完整响应 JSON)")
    parser.add_argument("-o", "--output", help="输出文件路径(默认: <input>_core.json)")
    parser.add_argument("--no-pretty", action="store_true", help="不格式化 JSON 输出")

    args = parser.parse_args()

    filter_response(
        input_file=args.input_file,
        output_file=args.output,
        pretty=not args.no_pretty,
    )


if __name__ == "__main__":
    main()
