"""
视频搜索脚本
支持多种排序方式、获取详细信息、导出结果
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from bilibili_api import search, video

# 支持直接运行和模块导入
try:
    from .utils import clean_title, format_number, format_timestamp, print_header
except ImportError:
    from utils import clean_title, format_number, format_timestamp, print_header


class VideoSearcher:
    """视频搜索工具"""

    def __init__(self, output_dir: str = "./search_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []

    async def search(
        self,
        keyword: str,
        order_type: search.OrderVideo = search.OrderVideo.TOTALRANK,
        page: int = 1,
        page_size: int = 20,
        get_details: bool = False
    ) -> List[Dict]:
        """
        搜索视频

        Args:
            keyword: 搜索关键词
            order_type: 排序方式
            page: 页码
            page_size: 每页数量
            get_details: 是否获取详细信息

        Returns:
            视频列表
        """
        print_header(f"🔍 搜索视频: {keyword}")
        print(f"📊 排序: {order_type.name}  |  📄 第{page}页  |  📦 每页{page_size}条")

        try:
            result = await search.search_by_type(
                keyword=keyword,
                search_type=search.SearchObjectType.VIDEO,
                order_type=order_type,
                page=page,
                page_size=page_size
            )

            videos = result.get('result', [])

            if not videos:
                print("❌ 未找到相关视频")
                return []

            print(f"\n✅ 找到 {len(videos)} 个视频")

            # 获取详细信息
            if get_details:
                print("\n⏳ 正在获取详细信息...")
                for i, v in enumerate(videos, 1):
                    bvid = v.get('bvid', '')
                    title = clean_title(v.get('title', ''))
                    print(f"   [{i}/{len(videos)}] {title[:40]}...")

                    try:
                        video_obj = video.Video(bvid=bvid)
                        detail = await video_obj.get_info()
                        v['detail'] = detail

                        # 获取标签
                        try:
                            tags = await video_obj.get_tags()
                            v['tags'] = [t.get('tag_name') for t in tags]
                        except:
                            v['tags'] = []

                        # 获取分P
                        try:
                            pages = await video_obj.get_pages()
                            v['pages'] = pages
                        except:
                            v['pages'] = []

                        await asyncio.sleep(0.3)  # 避免请求过快
                    except Exception as e:
                        print(f"      ⚠️ 获取详情失败: {e}")
                        v['detail_error'] = str(e)

            # 保存结果
            self.results.extend(videos)
            return videos

        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []

    def print_results(self, limit: Optional[int] = None):
        """打印搜索结果"""
        if not self.results:
            print("\n❌ 暂无搜索结果")
            return

        results = self.results[:limit] if limit else self.results

        print_header(f"📹 搜索结果 (共 {len(results)} 个)")

        for i, v in enumerate(results, 1):
            title = clean_title(v.get('title', '无标题'))
            bvid = v.get('bvid', '')
            author = v.get('author', '未知')
            play = format_number(v.get('play', 0))
            duration = v.get('duration', '未知')

            print(f"\n[{i}] {title}")
            print(f"    UP主: {author}  |  播放: {play}  |  时长: {duration}")
            print(f"    BV: {bvid}")
            print(f"    链接: https://www.bilibili.com/video/{bvid}")

    def save_json(self, filename: str = None) -> str:
        """保存为 JSON 格式"""
        if filename is None:
            filename = f"video_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.output_dir / filename

        output_data = {
            'search_time': datetime.now().isoformat(),
            'total_count': len(self.results),
            'videos': self.results
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 JSON 已保存: {filepath}")
        return str(filepath)

    def save_markdown(self, filename: str = None) -> str:
        """保存为 Markdown 报告"""
        if filename is None:
            filename = f"video_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        filepath = self.output_dir / filename

        md_lines = [
            "# 视频搜索报告\n",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**结果数量**: {len(self.results)} 个\n",
            "\n---\n"
        ]

        for i, v in enumerate(self.results, 1):
            title = clean_title(v.get('title', '无标题'))
            bvid = v.get('bvid', '')
            author = v.get('author', '未知')
            play = format_number(v.get('play', 0))
            duration = v.get('duration', '未知')
            pubdate = format_timestamp(v.get('pubdate', 0))

            # 如果有详细信息
            if 'detail' in v:
                detail = v['detail']
                stat = detail.get('stat', {})
                desc = detail.get('desc', '')[:200]
                tags = v.get('tags', [])

                md_lines.extend([
                    f"## {i}. {title}\n\n",
                    f"| 项目 | 内容 |\n",
                    f"|------|------|\n",
                    f"| **BVID** | {bvid} |\n",
                    f"| **AV号** | av{detail.get('aid', 'N/A')} |\n",
                    f"| **UP主** | {author} |\n",
                    f"| **播放量** | {format_number(stat.get('view', 0))} |\n",
                    f"| **点赞** | {format_number(stat.get('like', 0))} |\n",
                    f"| **投币** | {format_number(stat.get('coin', 0))} |\n",
                    f"| **收藏** | {format_number(stat.get('favorite', 0))} |\n",
                    f"| **时长** | {duration} |\n",
                    f"| **发布时间** | {pubdate} |\n",
                    f"| **链接** | [观看](https://www.bilibili.com/video/{bvid}) |\n",
                ])

                if tags:
                    md_lines.append(f"| **标签** | {', '.join(tags)} |\n")

                md_lines.extend([
                    "\n### 简介\n\n",
                    f"{desc}...\n",
                    "\n---\n"
                ])
            else:
                md_lines.extend([
                    f"## {i}. {title}\n\n",
                    f"| 项目 | 内容 |\n",
                    f"|------|------|\n",
                    f"| **BVID** | {bvid} |\n",
                    f"| **UP主** | {author} |\n",
                    f"| **播放量** | {play} |\n",
                    f"| **时长** | {duration} |\n",
                    f"| **发布时间** | {pubdate} |\n",
                    f"| **链接** | [观看](https://www.bilibili.com/video/{bvid}) |\n",
                    "\n---\n"
                ])

        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(md_lines)

        print(f"📝 Markdown 已保存: {filepath}")
        return str(filepath)


# ============================================================
# 命令行使用
# ============================================================

async def main():
    """命令行入口"""
    import sys

    # 从命令行获取关键词
    if len(sys.argv) > 1:
        keyword = ' '.join(sys.argv[1:])
    else:
        keyword = input("请输入搜索关键词: ")

    searcher = VideoSearcher()

    # 搜索视频
    await searcher.search(
        keyword=keyword,
        order_type=search.OrderVideo.CLICK,  # 按播放量排序
        page_size=10,
        get_details=True  # 获取详细信息
    )

    # 打印结果
    searcher.print_results(limit=5)

    # 导出
    searcher.save_json()
    searcher.save_markdown()


if __name__ == "__main__":
    asyncio.run(main())
