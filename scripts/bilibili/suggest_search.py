"""
搜索建议脚本
获取关键词联想词
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List

from bilibili_api import search

# 支持直接运行和模块导入
try:
    from .utils import print_header
except ImportError:
    from utils import print_header


class SuggestSearcher:
    """搜索建议工具"""

    def __init__(self, output_dir: str = "./search_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.history = []

    async def fetch(self, keyword: str) -> List[str]:
        """
        获取搜索建议

        Args:
            keyword: 关键词

        Returns:
            建议列表
        """
        print_header(f"💡 获取「{keyword}」的搜索建议")

        try:
            suggests = await search.get_suggest_keywords(keyword)
            print(f"\n✅ 找到 {len(suggests)} 个建议")

            # 保存历史
            self.history.append({
                'keyword': keyword,
                'suggests': suggests,
                'time': datetime.now().isoformat()
            })

            return suggests
        except Exception as e:
            print(f"❌ 获取建议失败: {e}")
            return []

    def print_results(self, keyword: str = None, limit: int = 10):
        """打印搜索建议"""
        if not self.history:
            print("\n❌ 暂无搜索建议历史")
            return

        # 查找指定关键词
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
            # 使用最近一次
            results = self.history[-1]['suggests']
            keyword = self.history[-1]['keyword']

        results = results[:limit]

        print_header(f"💡 「{keyword}」的搜索建议 (共 {len(results)} 个)")

        for i, s in enumerate(results, 1):
            print(f"{i:2}. {s}")

    def save_json(self, filename: str = None) -> str:
        """保存为 JSON 格式"""
        if filename is None:
            filename = f"suggest_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.output_dir / filename

        output_data = {
            'fetch_time': datetime.now().isoformat(),
            'total_queries': len(self.history),
            'history': self.history
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 JSON 已保存: {filepath}")
        return str(filepath)

    def save_markdown(self, filename: str = None) -> str:
        """保存为 Markdown 报告"""
        if filename is None:
            filename = f"suggest_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        filepath = self.output_dir / filename

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
        keyword = input("请输入关键词: ")

    searcher = SuggestSearcher()

    # 获取搜索建议
    await searcher.fetch(keyword)

    # 打印结果
    searcher.print_results()

    # 导出
    searcher.save_json()
    searcher.save_markdown()


if __name__ == "__main__":
    asyncio.run(main())
