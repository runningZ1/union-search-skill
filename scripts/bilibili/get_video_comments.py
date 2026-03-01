"""获取视频评论（含二级评论）- 需要登录凭证"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from bilibili_api import comment, video

try:
    from .config import get_credential
    from .utils import print_header, print_section
except ImportError:
    from config import get_credential
    from utils import print_header, print_section


class CommentFetcher:
    """评论获取器"""

    def __init__(self, output_dir: str = "./output"):
        self.credential = get_credential()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.all_comments: List[Dict] = []

    async def fetch_video_comments(
        self,
        bvid: str,
        order_type: comment.OrderType = comment.OrderType.TIME,
        max_pages: int = None
    ) -> List[Dict]:
        """获取视频的所有评论（含二级评论）"""
        print_header(f"开始获取视频评论：{bvid}")

        v = video.Video(bvid=bvid, credential=self.credential)
        info = await v.get_info()
        aid = info.get("aid")

        print(f"\n📺 视频：{info.get('title')}")
        print(f"   UP 主：{info.get('owner', {}).get('name')}")
        print(f"   总评论：{info.get('stat', {}).get('reply', 0)}")

        # 获取第一页确定总页数
        first_page = await comment.get_comments(
            oid=aid, type_=comment.CommentResourceType.VIDEO,
            page_index=1, order=order_type, credential=self.credential
        )

        total_count = first_page.get('page', {}).get('count', 0)
        page_size = 20
        total_pages = (total_count + page_size - 1) // page_size

        if max_pages:
            total_pages = min(total_pages, max_pages)
            print(f"   实际获取：{total_pages} 页")

        self.all_comments = []

        for page_num in range(1, total_pages + 1):
            print(f"\n📄 获取第 {page_num}/{total_pages} 页...")

            try:
                result = await comment.get_comments(
                    oid=aid, type_=comment.CommentResourceType.VIDEO,
                    page_index=page_num, order=order_type, credential=self.credential
                )

                replies = result.get('replies', [])
                if not replies:
                    continue

                for reply in replies:
                    comment_data = self._parse_comment(reply, bvid)
                    self.all_comments.append(comment_data)

                    # 获取二级评论
                    if reply.get('rcount', 0) > 0:
                        sub_comments = await self._fetch_sub_comments(aid, reply.get('rpid'), bvid)
                        self.all_comments.extend(sub_comments)

                print(f"  获取到 {len(replies)} 条评论")
                await asyncio.sleep(0.3)

            except Exception as e:
                print(f"  ❌ 获取失败：{e}")

        print(f"\n✅ 获取完成！共 {len(self.all_comments)} 条评论（含二级评论）")
        return self.all_comments

    async def _fetch_sub_comments(self, aid: int, root_rpid: int, bvid: str) -> List[Dict]:
        """获取二级评论"""
        try:
            parent_comment = comment.Comment(
                rpid=root_rpid, type_=comment.CommentResourceType.VIDEO,
                oid=aid, credential=self.credential
            )
            result = await parent_comment.get_sub_comments(page_index=1, page_size=20)

            sub_comments = []
            for sub in result.get('replies', []):
                sub_comments.append(self._parse_comment(sub, bvid, is_reply=True))
            return sub_comments

        except Exception as e:
            print(f"    ⚠️ 获取二级评论失败：{e}")
            return []

    def _parse_comment(self, reply: dict, bvid: str, is_reply: bool = False) -> dict:
        """解析评论数据"""
        member = reply.get('member', {})
        content_obj = reply.get('content', {})
        reply_control = reply.get('reply_control', {})
        level_info = member.get('level_info')

        # 提取表情
        emotes = []
        emote_data = content_obj.get('emote')
        if emote_data:
            if isinstance(emote_data, dict):
                for emote in emote_data.values():
                    if isinstance(emote, dict):
                        emotes.append({'text': emote.get('text', ''), 'url': emote.get('url', '')})
            elif isinstance(emote_data, list):
                for emote in emote_data:
                    if isinstance(emote, dict):
                        emotes.append({'text': emote.get('text', ''), 'url': emote.get('url', '')})

        # 提取跳转链接
        jump_urls = []
        jump_data = content_obj.get('jump_url')
        if jump_data and isinstance(jump_data, list):
            for jump in jump_data:
                if isinstance(jump, dict):
                    jump_urls.append({'title': jump.get('title', ''), 'url': jump.get('pc_url', '')})

        return {
            'bvid': bvid,
            'rpid': reply.get('rpid'),
            'parent_rpid': reply.get('parent'),
            'root_rpid': reply.get('root'),
            'is_reply': is_reply,
            'user': {
                'mid': member.get('mid'),
                'name': member.get('uname'),
                'avatar': member.get('avatar'),
                'level': level_info.get('current_level') if isinstance(level_info, dict) else level_info
            },
            'content': {
                'message': content_obj.get('message', ''),
                'emotes': emotes,
                'jump_urls': jump_urls
            },
            'like': reply.get('like', 0),
            'reply_count': reply.get('rcount', 0),
            'ctime': reply.get('ctime'),
            'ctime_formatted': datetime.fromtimestamp(reply.get('ctime', 0)).strftime('%Y-%m-%d %H:%M:%S'),
            'time_desc': reply_control.get('time_desc', '') if isinstance(reply_control, dict) else '',
            'up_action': reply.get('up_action', {}),
            'invisible': reply.get('invisible', False)
        }

    def save_json(self, filename: str = None) -> str:
        """保存为 JSON"""
        if filename is None:
            filename = f"comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename

        output_data = {
            'fetch_time': datetime.now().isoformat(),
            'total_count': len(self.all_comments),
            'comments': self.all_comments
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 JSON 已保存：{filepath}")
        return str(filepath)

    def save_markdown(self, filename: str = None) -> str:
        """保存为 Markdown"""
        if filename is None:
            filename = f"comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = self.output_dir / filename

        md_lines = [
            "# 视频评论报告\n",
            f"**获取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**评论总数**: {len(self.all_comments)}\n",
            "\n---\n"
        ]

        current_root = None
        for cmt in self.all_comments:
            if not cmt['is_reply']:
                if current_root is not None:
                    md_lines.append("\n---\n")
                current_root = cmt
                md_lines.extend([
                    f"## @{cmt['user']['name']} ({cmt['like']}赞)\n",
                    f"\n{cmt['content']['message']}\n",
                    f"\n*{cmt['time_desc']} · {cmt['reply_count']}条回复*\n"
                ])
                if cmt['content']['emotes']:
                    md_lines.append(f"\n**表情**: {', '.join([e['text'] for e in cmt['content']['emotes']])}\n")
            else:
                md_lines.extend([
                    f"\n### 💬 @{cmt['user']['name']}\n",
                    f"{cmt['content']['message']}\n",
                    f"\n*{cmt['time_desc']} · {cmt['like']}赞*\n"
                ])

        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(md_lines)
        print(f"📝 Markdown 已保存：{filepath}")
        return str(filepath)


async def main():
    """命令行入口"""
    import sys

    bvid = sys.argv[1].strip() if len(sys.argv) > 1 else input("请输入视频 BVID: ").strip()
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else None

    fetcher = CommentFetcher()
    await fetcher.fetch_video_comments(bvid, max_pages=max_pages)
    fetcher.save_json()
    fetcher.save_markdown()
    print("\n🎉 完成！")


if __name__ == "__main__":
    asyncio.run(main())
