"""
B 站搜索工具 - 统一搜索接口
支持视频搜索、用户搜索、热搜榜、搜索建议
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# bilibili_api 的路径配置在 __init__.py 中处理
from bilibili_api import search, video

# 支持直接运行和模块导入
try:
    from .utils import clean_title, format_number, format_timestamp, print_header
except ImportError:
    from utils import clean_title, format_number, format_timestamp, print_header


class BaseSearcher:
    """搜索器基类"""

    def __init__(self, output_dir: str = "./search_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []
        self.history = []

    def save_json(self, data: dict, filename: str = None) -> str:
        """保存为 JSON"""
        if filename is None:
            filename = f"{self.__class__.__name__.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 JSON 已保存：{filepath}")
        return str(filepath)

    def save_markdown(self, lines: list, filename: str = None) -> str:
        """保存为 Markdown"""
        if filename is None:
            filename = f"{self.__class__.__name__.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"📝 Markdown 已保存：{filepath}")
        return str(filepath)


class VideoSearcher(BaseSearcher):
    """视频搜索器"""

    async def search(
        self,
        keyword: str,
        order_type: search.OrderVideo = search.OrderVideo.TOTALRANK,
        page: int = 1,
        page_size: int = 20,
        get_details: bool = False
    ) -> List[Dict]:
        """搜索视频"""
        print_header(f"🔍 搜索视频：{keyword}")
        print(f"📊 排序：{order_type.name} | 📄 第{page}页 | 📦 每页{page_size}条")

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
                    v['tags'] = [t.get('tag_name') for t in await video_obj.get_tags()]
                    v['pages'] = await video_obj.get_pages()
                    await asyncio.sleep(0.3)
                except Exception as e:
                    print(f"      ⚠️ 获取详情失败：{e}")
                    v['detail_error'] = str(e)

        self.results.extend(videos)
        return videos

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
            print(f"    UP 主：{author} | 播放：{play} | 时长：{duration}")
            print(f"    BV: {bvid}")
            print(f"    链接：https://www.bilibili.com/video/{bvid}")

    def export(self, fmt: str = "both") -> Dict[str, str]:
        """导出结果"""
        if not self.results:
            return {}

        output_data = {
            'search_time': datetime.now().isoformat(),
            'total_count': len(self.results),
            'videos': self.results
        }

        files = {}
        if fmt in ("json", "both"):
            files['json'] = self.save_json(output_data, f"video_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        if fmt in ("md", "both"):
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

                if 'detail' in v:
                    detail = v['detail']
                    stat = detail.get('stat', {})
                    desc = detail.get('desc', '')[:200]
                    tags = v.get('tags', [])
                    md_lines.extend([
                        f"## {i}. {title}\n\n",
                        f"| 项目 | 内容 |\n|------|------|\n",
                        f"| **BVID** | {bvid} |\n| **AV 号** | av{detail.get('aid', 'N/A')} |\n",
                        f"| **UP 主** | {author} |\n| **播放量** | {format_number(stat.get('view', 0))} |\n",
                        f"| **点赞** | {format_number(stat.get('like', 0))} |\n| **投币** | {format_number(stat.get('coin', 0))} |\n",
                        f"| **收藏** | {format_number(stat.get('favorite', 0))} |\n| **时长** | {duration} |\n",
                        f"| **发布时间** | {pubdate} |\n| **链接** | [观看](https://www.bilibili.com/video/{bvid}) |\n",
                    ])
                    if tags:
                        md_lines.append(f"| **标签** | {', '.join(tags)} |\n")
                    md_lines.extend(["\n### 简介\n\n", f"{desc}...\n", "\n---\n"])
                else:
                    md_lines.extend([
                        f"## {i}. {title}\n\n",
                        f"| 项目 | 内容 |\n|------|------|\n",
                        f"| **BVID** | {bvid} |\n| **UP 主** | {author} |\n",
                        f"| **播放量** | {play} |\n| **时长** | {duration} |\n",
                        f"| **发布时间** | {pubdate} |\n| **链接** | [观看](https://www.bilibili.com/video/{bvid}) |\n",
                        "\n---\n"
                    ])
            files['md'] = self.save_markdown(md_lines, f"video_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        return files


class UserSearcher(BaseSearcher):
    """用户搜索器"""

    async def search(
        self,
        keyword: str,
        order_type: search.OrderUser = search.OrderUser.FANS,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict]:
        """搜索用户"""
        print_header(f"👤 搜索用户：{keyword}")
        print(f"📊 排序：{order_type.name} | 📄 第{page}页 | 📦 每页{page_size}条")

        result = await search.search_by_type(
            keyword=keyword,
            search_type=search.SearchObjectType.USER,
            order_type=order_type,
            page=page,
            page_size=page_size
        )

        users = result.get('result', [])
        if not users:
            print("❌ 未找到相关用户")
            return []

        print(f"\n✅ 找到 {len(users)} 个用户")
        self.results.extend(users)
        return users

    def print_results(self, limit: Optional[int] = None):
        """打印搜索结果"""
        if not self.results:
            print("\n❌ 暂无搜索结果")
            return

        results = self.results[:limit] if limit else self.results
        print_header(f"👤 搜索结果 (共 {len(results)} 个)")

        for i, u in enumerate(results, 1):
            name = u.get('uname', '未知')
            mid = u.get('mid', '')
            fans = format_number(u.get('fans', 0))
            level = u.get('level', 0)
            sign = clean_title(u.get('usign', ''))

            print(f"\n[{i}] {name} (Lv.{level})")
            print(f"    UID: {mid} | 粉丝：{fans}")
            if sign:
                print(f"    简介：{sign[:60]}...")

    def export(self, fmt: str = "both") -> Dict[str, str]:
        """导出结果"""
        if not self.results:
            return {}

        output_data = {
            'search_time': datetime.now().isoformat(),
            'total_count': len(self.results),
            'users': self.results
        }

        files = {}
        if fmt in ("json", "both"):
            files['json'] = self.save_json(output_data, f"user_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        if fmt in ("md", "both"):
            md_lines = [
                "# 用户搜索报告\n",
                f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                f"**结果数量**: {len(self.results)} 个\n",
                "\n---\n"
            ]
            for i, u in enumerate(self.results, 1):
                name = u.get('uname', '未知')
                mid = u.get('mid', '')
                fans = format_number(u.get('fans', 0))
                level = u.get('level', 0)
                sign = clean_title(u.get('usign', ''))
                avatar = u.get('upic', '')

                md_lines.extend([
                    f"## {i}. {name} (Lv.{level})\n\n",
                    f"| 项目 | 内容 |\n|------|------|\n",
                    f"| **UID** | {mid} |\n| **粉丝数** | {fans} |\n",
                    f"| **等级** | {level} |\n",
                ])
                if sign:
                    md_lines.append(f"| **简介** | {sign[:100]}... |\n")
                if avatar:
                    md_lines.append(f"| **头像** | ![{name}]({avatar}) |\n")
                md_lines.append("\n---\n")
            files['md'] = self.save_markdown(md_lines, f"user_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        return files


class HotSearcher(BaseSearcher):
    """热搜榜搜索器"""

    async def fetch(self, limit: int = 30) -> List[Dict]:
        """获取热搜榜"""
        print_header(f"🔥 获取热搜榜 Top {limit}")

        hot_data = await search.get_hot_search_keywords()
        if isinstance(hot_data, dict) and "list" in hot_data:
            hot_list = hot_data["list"][:limit]
            print(f"\n✅ 获取成功，共 {len(hot_list)} 条热搜")
            self.results = hot_list
            return hot_list
        else:
            print("❌ 热搜数据格式异常")
            return []

    def print_results(self, limit: Optional[int] = None):
        """打印热搜榜"""
        if not self.results:
            print("\n❌ 暂无热搜数据")
            return

        results = self.results[:limit] if limit else self.results
        print_header(f"📊 热搜榜 (共 {len(results)} 条)")

        for i, item in enumerate(results, 1):
            keyword = item.get('keyword', '未知')
            heat = item.get('heat_score', 0)
            heat_layer = item.get('heat_layer', '')
            icon = {"S": "🔥", "A": "⚡", "B": "📈"}.get(heat_layer, "📊")
            print(f"\n{i:2}. {icon} {keyword}")
            print(f"    热度：{heat:,}")

    def export(self, fmt: str = "both") -> Dict[str, str]:
        """导出结果"""
        if not self.results:
            return {}

        output_data = {
            'fetch_time': datetime.now().isoformat(),
            'total_count': len(self.results),
            'hot_list': self.results
        }

        files = {}
        if fmt in ("json", "both"):
            files['json'] = self.save_json(output_data, f"hot_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        if fmt in ("md", "both"):
            md_lines = [
                "# B 站热搜榜\n",
                f"**获取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                f"**热搜数量**: {len(self.results)} 条\n",
                "\n---\n\n",
                "| 排名 | 热度等级 | 关键词 | 热度值 |\n|------|----------|--------|--------|\n"
            ]
            for i, item in enumerate(self.results, 1):
                keyword = item.get('keyword', '未知')
                heat = item.get('heat_score', 0)
                heat_layer = item.get('heat_layer', '')
                icon = {"S": "🔥", "A": "⚡", "B": "📈"}.get(heat_layer, "")
                md_lines.append(f"| {i} | {icon} {heat_layer} | {keyword} | {heat:,} |\n")
            files['md'] = self.save_markdown(md_lines, f"hot_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        return files


class SuggestSearcher(BaseSearcher):
    """搜索建议搜索器"""

    async def fetch(self, keyword: str) -> List[str]:
        """获取搜索建议"""
        print_header(f"💡 获取「{keyword}」的搜索建议")

        suggests = await search.get_suggest_keywords(keyword)
        print(f"\n✅ 找到 {len(suggests)} 个建议")

        self.history.append({
            'keyword': keyword,
            'suggests': suggests,
            'time': datetime.now().isoformat()
        })
        return suggests

    def print_results(self, keyword: str = None, limit: int = 10):
        """打印搜索建议"""
        if not self.history:
            print("\n❌ 暂无搜索建议历史")
            return

        results = []
        if keyword:
            for h in self.history:
                if h['keyword'] == keyword:
                    results = h['suggests']
                    break
            if not results:
                print(f"\n❌ 未找到「{keyword}」的搜索建议")
                return
        else:
            results = self.history[-1]['suggests']
            keyword = self.history[-1]['keyword']

        results = results[:limit]
        print_header(f"💡 「{keyword}」的搜索建议 (共 {len(results)} 个)")

        for i, s in enumerate(results, 1):
            print(f"{i:2}. {s}")

    def export(self, fmt: str = "both") -> Dict[str, str]:
        """导出结果"""
        if not self.history:
            return {}

        output_data = {
            'fetch_time': datetime.now().isoformat(),
            'total_queries': len(self.history),
            'history': self.history
        }

        files = {}
        if fmt in ("json", "both"):
            files['json'] = self.save_json(output_data, f"suggest_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        if fmt in ("md", "both"):
            md_lines = [
                "# 搜索建议报告\n",
                f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                f"**查询数量**: {len(self.history)} 个\n",
                "\n---\n"
            ]
            for h in self.history:
                keyword = h['keyword']
                suggests = h['suggests']
                md_lines.extend([
                    f"## 「{keyword}」的搜索建议\n\n",
                    f"共 {len(suggests)} 个建议：\n\n"
                ])
                for i, s in enumerate(suggests, 1):
                    md_lines.append(f"{i}. {s}\n")
                md_lines.append("\n---\n")
            files['md'] = self.save_markdown(md_lines, f"suggest_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        return files


# ============================================================
# 命令行入口
# ============================================================

async def main():
    """命令行入口"""
    import sys

    if len(sys.argv) < 2:
        print("用法：python search.py <type> <keyword|limit>")
        print("类型：video | user | hot | suggest")
        sys.exit(1)

    search_type = sys.argv[1].lower()

    if search_type == "video":
        keyword = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else input("请输入搜索关键词：")
        searcher = VideoSearcher()
        await searcher.search(keyword=keyword, page_size=10, get_details=False)
        searcher.print_results(limit=5)
    elif search_type == "user":
        keyword = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else input("请输入搜索关键词：")
        searcher = UserSearcher()
        await searcher.search(keyword=keyword, page_size=10)
        searcher.print_results()
    elif search_type == "hot":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        searcher = HotSearcher()
        await searcher.fetch(limit=limit)
        searcher.print_results()
    elif search_type == "suggest":
        keyword = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else input("请输入关键词：")
        searcher = SuggestSearcher()
        await searcher.fetch(keyword)
        searcher.print_results()
    else:
        print(f"未知类型：{search_type}")
        sys.exit(1)

    # 统一导出
    searcher.export()


if __name__ == "__main__":
    asyncio.run(main())
