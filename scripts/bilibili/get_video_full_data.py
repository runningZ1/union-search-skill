"""
B站视频数据获取脚本
获取视频的所有基本信息、统计数据、分P信息、标签等
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from bilibili_api import video


async def get_all_video_data(bvid: str) -> dict:
    """
    获取视频的所有数据

    Args:
        bvid: 视频的BVID

    Returns:
        包含所有视频数据的字典
    """
    print(f"开始获取视频数据: {bvid}")
    print("=" * 60)

    v = video.Video(bvid=bvid)
    data = {
        "bvid": bvid,
        "fetch_time": datetime.now().isoformat()
    }

    # 1. 获取视频基本信息
    print("\n📺 获取视频基本信息...")
    info = await v.get_info()
    data["basic_info"] = {
        "title": info.get("title"),
        "bvid": bvid,
        "aid": info.get("aid"),
        "desc": info.get("desc"),
        "pubdate": info.get("pubdate"),
        "pubdate_formatted": datetime.fromtimestamp(info.get("pubdate", 0)).strftime("%Y-%m-%d %H:%M:%S"),
        "duration": info.get("duration"),
        "owner": {
            "mid": info.get("owner", {}).get("mid"),
            "name": info.get("owner", {}).get("name"),
            "face": info.get("owner", {}).get("face")
        },
        "pic": info.get("pic"),
        "cid": info.get("cid")
    }
    print(f"  标题: {data['basic_info']['title']}")
    print(f"  UP主: {data['basic_info']['owner']['name']}")
    print(f"  发布时间: {data['basic_info']['pubdate_formatted']}")

    # 2. 获取统计数据
    print("\n📊 获取统计数据...")
    stat = info.get("stat", {})
    data["statistics"] = {
        "view": stat.get("view", 0),
        "danmaku": stat.get("danmaku", 0),
        "reply": stat.get("reply", 0),
        "favorite": stat.get("favorite", 0),
        "coin": stat.get("coin", 0),
        "share": stat.get("share", 0),
        "like": stat.get("like", 0),
        "dislike": stat.get("dislike", 0)
    }
    print(f"  播放: {data['statistics']['view']:,}")
    print(f"  点赞: {data['statistics']['like']:,}")
    print(f"  投币: {data['statistics']['coin']:,}")
    print(f"  收藏: {data['statistics']['favorite']:,}")
    print(f"  评论: {data['statistics']['reply']:,}")

    # 3. 获取分P信息
    print("\n🎬 获取分P信息...")
    pages = await v.get_pages()
    data["pages"] = []
    for idx, page in enumerate(pages, 1):
        page_info = {
            "page": idx,
            "cid": page.get("cid"),
            "part": page.get("part"),
            "duration": page.get("duration"),
            "duration_formatted": f"{page.get('duration') // 60}:{page.get('duration') % 60:02d}",
            "vid": page.get("vid"),
            "weblink": page.get("weblink")
        }
        data["pages"].append(page_info)
        print(f"  P{idx}: {page_info['part']} ({page_info['duration_formatted']})")

    # 4. 获取标签
    print("\n🏷️ 获取标签...")
    tags = await v.get_tags()
    data["tags"] = []
    for tag in tags:
        tag_info = {
            "tag_id": tag.get("tag_id"),
            "tag_name": tag.get("tag_name"),
            "jump_url": tag.get("jump_url")
        }
        data["tags"].append(tag_info)
    print(f"  共 {len(tags)} 个标签: {', '.join([t['tag_name'] for t in data['tags']])}")

    # 5. 获取字幕
    print("\n💬 获取字幕信息...")
    try:
        # 获取cid
        if not data["basic_info"]["cid"]:
            raise Exception("无法获取cid")
        else:
            cid = data["basic_info"]["cid"]

        subtitle_data = await v.get_subtitle(cid=cid)
        data["subtitles"] = []
        if subtitle_data:
            # subtitle_data 可能是 dict 或 list
            if isinstance(subtitle_data, dict):
                subtitle_list = subtitle_data.get("subtitles", [])
            elif isinstance(subtitle_data, list):
                subtitle_list = subtitle_data
            else:
                subtitle_list = []

            for sub in subtitle_list:
                subtitle_info = {
                    "id": sub.get("id"),
                    "lan": sub.get("lan"),
                    "lan_doc": sub.get("lan_doc"),
                    "subtitle_url": sub.get("subtitle_url")
                }
                data["subtitles"].append(subtitle_info)
            print(f"  共 {len(data['subtitles'])} 个字幕")
        else:
            print("  无字幕")
    except Exception as e:
        print(f"  获取字幕失败: {e}")
        data["subtitles"] = []

    # 6. 获取相关视频
    print("\n🔗 获取相关推荐...")
    try:
        related = await v.get_related()
        data["related_videos"] = []
        for rel in related[:10]:  # 只取前10个
            rel_info = {
                "bvid": rel.get("bvid"),
                "title": rel.get("title"),
                "owner": {
                    "mid": rel.get("owner", {}).get("mid"),
                    "name": rel.get("owner", {}).get("name")
                },
                "stat": {
                    "view": rel.get("stat", {}).get("view"),
                    "danmaku": rel.get("stat", {}).get("danmaku")
                }
            }
            data["related_videos"].append(rel_info)
        print(f"  获取到 {len(data['related_videos'])} 个相关推荐")
    except Exception as e:
        print(f"  获取相关推荐失败: {e}")
        data["related_videos"] = []

    # 7. 获取弹幕
    print("\n💥 获取弹幕...")
    try:
        danmakus = await v.get_danmakus()
        data["danmaku_count"] = len(danmakus)
        data["danmakus_sample"] = []
        for dm in danmakus[:20]:  # 只取前20条作为样本
            # dm_time 是弹幕在视频中的时间位置（秒）
            time_pos = dm.dm_time / 1000 if dm.dm_time else 0
            dm_info = {
                "text": dm.text,
                "dm_time": dm.dm_time,
                "time_position": f"{time_pos:.1f}s",
                "send_time": dm.send_time,
                "send_time_formatted": datetime.fromtimestamp(dm.send_time).strftime("%Y-%m-%d %H:%M:%S") if dm.send_time else "",
                "sender_id": dm.uid,
                "color": dm.color,
                "font_size": dm.font_size,
                "mode": dm.mode
            }
            data["danmakus_sample"].append(dm_info)
        print(f"  共 {data['danmaku_count']} 条弹幕 (已记录前20条样本)")
    except Exception as e:
        print(f"  获取弹幕失败: {e}")
        data["danmaku_count"] = 0
        data["danmakus_sample"] = []

    print("\n" + "=" * 60)
    print("✅ 所有数据获取完成！")

    return data


def save_to_json(data: dict, output_file: str = None):
    """保存为JSON文件"""
    if output_file is None:
        bvid = data["bvid"]
        output_file = f"video_data_{bvid}.json"

    output_path = Path(output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 JSON 已保存: {output_path.absolute()}")
    return str(output_path.absolute())


def save_to_markdown(data: dict, output_file: str = None):
    """保存为Markdown文件"""
    if output_file is None:
        bvid = data["bvid"]
        output_file = f"video_data_{bvid}.md"

    output_path = Path(output_file)

    md_lines = [
        "# B站视频数据报告\n",
        f"**BVID**: {data['bvid']}\n",
        f"**获取时间**: {datetime.fromisoformat(data['fetch_time']).strftime('%Y-%m-%d %H:%M:%S')}\n",
        "\n---\n",
        "## 📺 基本信息\n",
        f"- **标题**: {data['basic_info']['title']}\n",
        f"- **AV号**: {data['basic_info']['aid']}\n",
        f"- **UP主**: [{data['basic_info']['owner']['name']}](https://space.bilibili.com/{data['basic_info']['owner']['mid']})\n",
        f"- **发布时间**: {data['basic_info']['pubdate_formatted']}\n",
        f"- **时长**: {data['basic_info']['duration']}秒\n",
        f"- **简介**: {data['basic_info']['desc']}\n",
        "\n---\n",
        "## 📊 数据统计\n",
        f"| 指标 | 数值 |\n",
        f"|------|------|\n",
        f"| 播放量 | {data['statistics']['view']:,} |\n",
        f"| 点赞数 | {data['statistics']['like']:,} |\n",
        f"| 投币数 | {data['statistics']['coin']:,} |\n",
        f"| 收藏数 | {data['statistics']['favorite']:,} |\n",
        f"| 分享数 | {data['statistics']['share']:,} |\n",
        f"| 弹幕数 | {data['statistics']['danmaku']:,} |\n",
        f"| 评论数 | {data['statistics']['reply']:,} |\n",
        "\n---\n",
        "## 🎬 分P信息\n"
    ]

    for page in data["pages"]:
        md_lines.append(f"\n### P{page['page']}: {page['part']}\n")
        md_lines.append(f"- CID: {page['cid']}\n")
        md_lines.append(f"- 时长: {page['duration_formatted']}\n")

    md_lines.extend([
        "\n---\n",
        "## 🏷️ 标签\n"
    ])

    for tag in data["tags"]:
        md_lines.append(f"- {tag['tag_name']}\n")

    if data.get("subtitles"):
        md_lines.extend([
            "\n---\n",
            "## 💬 字幕\n"
        ])
        for sub in data["subtitles"]:
            md_lines.append(f"- {sub['lan_doc']}: {sub['subtitle_url']}\n")

    if data.get("related_videos"):
        md_lines.extend([
            "\n---\n",
            "## 🔗 相关推荐\n"
        ])
        for rel in data["related_videos"]:
            md_lines.append(f"\n#### [{rel['title']}](https://www.bilibili.com/video/{rel['bvid']})\n")
            md_lines.append(f"- UP主: {rel['owner']['name']}\n")
            md_lines.append(f"- 播放: {rel['stat']['view']:,}\n")

    if data.get("danmaku_count", 0) > 0:
        md_lines.extend([
            "\n---\n",
            f"## 💥 弹幕 (共{data['danmaku_count']:,}条，显示前20条)\n"
        ])
        for dm in data["danmakus_sample"]:
            md_lines.append(f"- [{dm.get('time_position', dm.get('time_formatted', ''))}] {dm['text']}\n")

    md_lines.append("\n---\n")
    md_lines.append(f"\n*报告生成时间: {data['fetch_time']}*\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(md_lines)

    print(f"📝 Markdown 已保存: {output_path.absolute()}")
    return str(output_path.absolute())


async def main():
    """主函数"""
    import sys

    # 从命令行获取BVID
    if len(sys.argv) > 1:
        bvid = sys.argv[1]
    else:
        bvid = input("请输入视频BVID: ").strip()

    # 获取所有数据
    data = await get_all_video_data(bvid)

    # 保存文件
    json_file = save_to_json(data)
    md_file = save_to_markdown(data)

    print("\n🎉 完成！")
    print(f"  - JSON: {json_file}")
    print(f"  - Markdown: {md_file}")

    print("\n⚠️ 注意：评论区需要登录才能获取，当前脚本未包含评论数据。")
    print("   如需获取评论，请使用 bilibili-api 的 Credential 功能进行登录。")


if __name__ == "__main__":
    asyncio.run(main())
