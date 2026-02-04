"""
热搜榜脚本
获取B站热搜榜数据
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
    from .utils import print_header
except ImportError:
    from utils import print_header


class HotSearcher:
    """热搜榜工具"""

    def __init__(self, output_dir: str = "./search_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []

    async def fetch(self, limit: int = 30) -> List[Dict]:
        """
        获取热搜榜

        Args:
            limit: 获取数量

        Returns:
            热搜列表
        """
        print_header(f"🔥 获取热搜榜 Top {limit}")

        try:
            hot_data = await search.get_hot_search_keywords()

            if isinstance(hot_data, dict) and "list" in hot_data:
                hot_list = hot_data["list"][:limit]
                print(f"\n✅ 获取成功，共 {len(hot_list)} 条热搜")

                self.results = hot_list
                return hot_list
            else:
                print("❌ 热搜数据格式异常")
                return []

        except Exception as e:
            print(f"❌ 获取热搜失败: {e}")
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

            # 热度图标
            icon = {"S": "🔥", "A": "⚡", "B": "📈"}.get(heat_layer, "📊")

            print(f"\n{i:2}. {icon} {keyword}")
            print(f"    热度: {heat:,}")

    def save_json(self, filename: str = None) -> str:
        """保存为 JSON 格式"""
        if filename is None:
            filename = f"hot_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.output_dir / filename

        output_data = {
            'fetch_time': datetime.now().isoformat(),
            'total_count': len(self.results),
            'hot_list': self.results
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 JSON 已保存: {filepath}")
        return str(filepath)

    def save_markdown(self, filename: str = None) -> str:
        """保存为 Markdown 报告"""
        if filename is None:
            filename = f"hot_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        filepath = self.output_dir / filename

        md_lines = [
            "# B站热搜榜\n",
            f"**获取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**热搜数量**: {len(self.results)} 条\n",
            "\n---\n\n",
            "| 排名 | 热度等级 | 关键词 | 热度值 |\n",
            "|------|----------|--------|--------|\n"
        ]

        for i, item in enumerate(self.results, 1):
            keyword = item.get('keyword', '未知')
            heat = item.get('heat_score', 0)
            heat_layer = item.get('heat_layer', '')

            icon = {"S": "🔥", "A": "⚡", "B": "📈"}.get(heat_layer, "")

            md_lines.append(f"| {i} | {icon} {heat_layer} | {keyword} | {heat:,} |\n")

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

    # 从命令行获取数量
    limit = 30
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except:
            pass

    searcher = HotSearcher()

    # 获取热搜
    await searcher.fetch(limit=limit)

    # 打印结果
    searcher.print_results()

    # 导出
    searcher.save_json()
    searcher.save_markdown()


if __name__ == "__main__":
    asyncio.run(main())
