"""获取视频完整数据（无需登录）"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from bilibili_api import video

try:
    from .utils import print_header
except ImportError:
    from utils import print_header


async def get_all_video_data(bvid: str) -> Dict:
    """获取视频的所有数据"""
    print_header(f"开始获取视频数据：{bvid}")

    v = video.Video(bvid=bvid)
    data = {"bvid": bvid, "fetch_time": datetime.now().isoformat()}

    # 1. 基本信息
    print("\n📺 获取基本信息...")
    info = await v.get_info()
    data["basic_info"] = {
        "title": info.get("title"),
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
    print(f"  标题：{data['basic_info']['title']}")
    print(f"  UP 主：{data['basic_info']['owner']['name']}")

    # 2. 统计数据
    print("\n📊 获取统计数据...")
    stat = info.get("stat", {})
    data["statistics"] = {
        "view": stat.get("view", 0),
        "danmaku": stat.get("danmaku", 0),
        "reply": stat.get("reply", 0),
        "favorite": stat.get("favorite", 0),
        "coin": stat.get("coin", 0),
        "share": stat.get("share", 0),
        "like": stat.get("like", 0)
    }
    print(f"  播放：{data['statistics']['view']:,} | 点赞：{data['statistics']['like']:,}")

    # 3. 分 P 信息
    print("\n🎬 获取分 P 信息...")
    data["pages"] = []
    for idx, page in enumerate(await v.get_pages(), 1):
        page_info = {
            "page": idx,
            "cid": page.get("cid"),
            "part": page.get("part"),
            "duration": page.get("duration"),
            "duration_formatted": f"{page.get('duration') // 60}:{page.get('duration') % 60:02d}"
        }
        data["pages"].append(page_info)
        print(f"  P{idx}: {page_info['part']} ({page_info['duration_formatted']})")

    # 4. 标签
    print("\n🏷️ 获取标签...")
    data["tags"] = []
    for tag in await v.get_tags():
        data["tags"].append({"tag_id": tag.get("tag_id"), "tag_name": tag.get("tag_name")})
    print(f"  共 {len(data['tags'])} 个标签：{', '.join([t['tag_name'] for t in data['tags']])}")

    # 5. 字幕
    print("\n💬 获取字幕...")
    data["subtitles"] = []
    try:
        cid = data["basic_info"]["cid"]
        if cid:
            subtitle_data = await v.get_subtitle(cid=cid)
            if subtitle_data:
                subtitle_list = subtitle_data.get("subtitles", []) if isinstance(subtitle_data, dict) else subtitle_data
                for sub in subtitle_list:
                    data["subtitles"].append({
                        "id": sub.get("id"),
                        "lan": sub.get("lan"),
                        "lan_doc": sub.get("lan_doc"),
                        "subtitle_url": sub.get("subtitle_url")
                    })
                print(f"  共 {len(data['subtitles'])} 个字幕")
            else:
                print("  无字幕")
    except Exception as e:
        print(f"  获取字幕失败：{e}")

    # 6. 相关推荐
    print("\n🔗 获取相关推荐...")
    data["related_videos"] = []
    try:
        related = await v.get_related()
        for rel in related[:10]:
            data["related_videos"].append({
                "bvid": rel.get("bvid"),
                "title": rel.get("title"),
                "owner": {"mid": rel.get("owner", {}).get("mid"), "name": rel.get("owner", {}).get("name")},
                "stat": {"view": rel.get("stat", {}).get("view"), "danmaku": rel.get("stat", {}).get("danmaku")}
            })
        print(f"  获取到 {len(data['related_videos'])} 个相关推荐")
    except Exception as e:
        print(f"  获取相关推荐失败：{e}")

    # 7. 弹幕
    print("\n💥 获取弹幕...")
    data["danmaku_count"] = 0
    data["danmakus_sample"] = []
    try:
        danmakus = await v.get_danmakus()
        data["danmaku_count"] = len(danmakus)
        for dm in danmakus[:20]:
            data["danmakus_sample"].append({
                "text": dm.text,
                "dm_time": dm.dm_time,
                "time_position": f"{dm.dm_time / 1000:.1f}s" if dm.dm_time else "0.0s",
                "send_time": dm.send_time,
                "send_time_formatted": datetime.fromtimestamp(dm.send_time).strftime("%Y-%m-%d %H:%M:%S") if dm.send_time else "",
                "sender_id": dm.uid,
                "color": dm.color,
                "font_size": dm.font_size,
                "mode": dm.mode
            })
        print(f"  共 {data['danmaku_count']} 条弹幕 (已记录前 20 条)")
    except Exception as e:
        print(f"  获取弹幕失败：{e}")

    print("\n" + "=" * 60)
    print("✅ 所有数据获取完成！")
    return data


def save_to_json(data: Dict, output_file: str = None) -> str:
    """保存为 JSON"""
    if output_file is None:
        output_file = f"video_data_{data['bvid']}.json"
    output_path = Path(output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 JSON 已保存：{output_path.absolute()}")
    return str(output_path.absolute())


def save_to_markdown(data: Dict, output_file: str = None) -> str:
    """保存为 Markdown"""
    if output_file is None:
        output_file = f"video_data_{data['bvid']}.md"
    output_path = Path(output_file)

    bi = data['basic_info']
    stats = data['statistics']

    md_lines = [
        "# B 站视频数据报告\n",
        f"**BVID**: {data['bvid']}\n",
        f"**获取时间**: {datetime.fromisoformat(data['fetch_time']).strftime('%Y-%m-%d %H:%M:%S')}\n",
        "\n---\n",
        "## 📺 基本信息\n",
        f"- **标题**: {bi['title']}\n",
        f"- **AV 号**: {bi['aid']}\n",
        f"- **UP 主**: [{bi['owner']['name']}](https://space.bilibili.com/{bi['owner']['mid']})\n",
        f"- **发布时间**: {bi['pubdate_formatted']}\n",
        f"- **时长**: {bi['duration']}秒\n",
        f"- **简介**: {bi['desc']}\n",
        "\n---\n",
        "## 📊 数据统计\n",
        "| 指标 | 数值 |\n|------|------|\n",
        f"| 播放量 | {stats['view']:,} |\n",
        f"| 点赞数 | {stats['like']:,} |\n",
        f"| 投币数 | {stats['coin']:,} |\n",
        f"| 收藏数 | {stats['favorite']:,} |\n",
        f"| 分享数 | {stats['share']:,} |\n",
        f"| 弹幕数 | {stats['danmaku']:,} |\n",
        f"| 评论数 | {stats['reply']:,} |\n",
        "\n---\n",
        "## 🎬 分 P 信息\n"
    ]

    for page in data["pages"]:
        md_lines.append(f"\n### P{page['page']}: {page['part']}\n")
        md_lines.append(f"- CID: {page['cid']}\n")
        md_lines.append(f"- 时长：{page['duration_formatted']}\n")

    md_lines.extend(["\n---\n", "## 🏷️ 标签\n"])
    for tag in data["tags"]:
        md_lines.append(f"- {tag['tag_name']}\n")

    if data.get("subtitles"):
        md_lines.extend(["\n---\n", "## 💬 字幕\n"])
        for sub in data["subtitles"]:
            md_lines.append(f"- {sub['lan_doc']}: {sub['subtitle_url']}\n")

    if data.get("related_videos"):
        md_lines.extend(["\n---\n", "## 🔗 相关推荐\n"])
        for rel in data["related_videos"]:
            md_lines.append(f"\n#### [{rel['title']}](https://www.bilibili.com/video/{rel['bvid']})\n")
            md_lines.append(f"- UP 主：{rel['owner']['name']}\n")
            md_lines.append(f"- 播放：{rel['stat']['view']:,}\n")

    if data.get("danmaku_count", 0) > 0:
        md_lines.extend(["\n---\n", f"## 💥 弹幕 (共{data['danmaku_count']:,}条，显示前 20 条)\n"])
        for dm in data["danmakus_sample"]:
            md_lines.append(f"- [{dm.get('time_position', '')}] {dm['text']}\n")

    md_lines.append(f"\n---\n\n*报告生成时间：{data['fetch_time']}*\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(md_lines)
    print(f"📝 Markdown 已保存：{output_path.absolute()}")
    return str(output_path.absolute())


async def main():
    """命令行入口"""
    import sys

    bvid = sys.argv[1].strip() if len(sys.argv) > 1 else input("请输入视频 BVID: ").strip()
    data = await get_all_video_data(bvid)
    json_file = save_to_json(data)
    md_file = save_to_markdown(data)
    print(f"\n🎉 完成！\n  - JSON: {json_file}\n  - Markdown: {md_file}")


if __name__ == "__main__":
    asyncio.run(main())
