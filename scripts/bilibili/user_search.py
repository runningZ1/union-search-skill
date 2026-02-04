"""
用户搜索脚本
支持按粉丝数/等级排序
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from bilibili_api import search

# 支持直接运行和模块导入
try:
    from .utils import clean_title, format_number, print_header
except ImportError:
    from utils import clean_title, format_number, print_header


class UserSearcher:
    """用户搜索工具"""

    def __init__(self, output_dir: str = "./search_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []

    async def search(
        self,
        keyword: str,
        order_type: search.OrderUser = search.OrderUser.FANS,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict]:
        """
        搜索用户

        Args:
            keyword: 搜索关键词
            order_type: 排序方式 (FANS=粉丝数, LEVEL=等级)
            page: 页码
            page_size: 每页数量

        Returns:
            用户列表
        """
        print_header(f"👤 搜索用户: {keyword}")
        print(f"📊 排序: {order_type.name}  |  📄 第{page}页  |  📦 每页{page_size}条")

        try:
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

        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []

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
            print(f"    UID: {mid}  |  粉丝: {fans}")
            if sign:
                print(f"    简介: {sign[:60]}...")

    def save_json(self, filename: str = None) -> str:
        """保存为 JSON 格式"""
        if filename is None:
            filename = f"user_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.output_dir / filename

        output_data = {
            'search_time': datetime.now().isoformat(),
            'total_count': len(self.results),
            'users': self.results
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 JSON 已保存: {filepath}")
        return str(filepath)

    def save_markdown(self, filename: str = None) -> str:
        """保存为 Markdown 报告"""
        if filename is None:
            filename = f"user_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        filepath = self.output_dir / filename

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
                f"| 项目 | 内容 |\n",
                f"|------|------|\n",
                f"| **UID** | {mid} |\n",
                f"| **粉丝数** | {fans} |\n",
                f"| **等级** | {level} |\n",
            ])

            if sign:
                md_lines.append(f"| **简介** | {sign[:100]}... |\n")

            if avatar:
                md_lines.append(f"| **头像** | ![{name}]({avatar}) |\n")

            md_lines.append("\n---\n")

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

    if len(sys.argv) > 1:
        keyword = ' '.join(sys.argv[1:])
    else:
        keyword = input("请输入搜索关键词: ")

    searcher = UserSearcher()

    # 搜索用户
    await searcher.search(
        keyword=keyword,
        order_type=search.OrderUser.FANS,  # 按粉丝数排序
        page_size=10
    )

    # 打印结果
    searcher.print_results()

    # 导出
    searcher.save_json()
    searcher.save_markdown()


if __name__ == "__main__":
    asyncio.run(main())
