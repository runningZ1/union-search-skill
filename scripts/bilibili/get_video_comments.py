"""
带登录凭证的评论获取脚本
获取视频的所有评论（包括一级和二级评论）
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from bilibili_api import comment, video
from config import get_credential


class CommentFetcher:
    """评论获取器"""

    def __init__(self, output_dir: str = "./output"):
        self.credential = get_credential()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.all_comments = []

    async def fetch_video_comments(
        self,
        bvid: str,
        order_type: comment.OrderType = comment.OrderType.TIME,
        max_pages: int = None
    ) -> list:
        """
        获取视频的所有评论

        Args:
            bvid: 视频BVID
            order_type: 排序方式（TIME/LIKE/HOT）
            max_pages: 最大获取页数（None表示获取全部）

        Returns:
            评论列表
        """
        print("=" * 70)
        print(f"开始获取视频评论: {bvid}")
        print("=" * 70)

        v = video.Video(bvid=bvid, credential=self.credential)
        info = await v.get_info()
        aid = info.get("aid")

        print(f"\n📺 视频信息:")
        print(f"  标题: {info.get('title')}")
        print(f"  UP主: {info.get('owner', {}).get('name')}")
        print(f"  总评论数: {info.get('stat', {}).get('reply', 0)}")

        # 获取第一页，确定总页数
        print(f"\n🔍 获取第一页评论...")
        first_page = await comment.get_comments(
            oid=aid,
            type_=comment.CommentResourceType.VIDEO,
            page_index=1,
            order=order_type,
            credential=self.credential
        )

        total_count = first_page.get('page', {}).get('count', 0)
        page_size = 20
        total_pages = (total_count + page_size - 1) // page_size

        print(f"  总评论数: {total_count}")
        print(f"  总页数: {total_pages}")

        # 限制获取页数
        if max_pages:
            total_pages = min(total_pages, max_pages)
            print(f"  实际获取: {total_pages} 页")

        self.all_comments = []

        # 遍历所有页
        for page_num in range(1, total_pages + 1):
            print(f"\n📄 获取第 {page_num}/{total_pages} 页...")

            try:
                result = await comment.get_comments(
                    oid=aid,
                    type_=comment.CommentResourceType.VIDEO,
                    page_index=page_num,
                    order=order_type,
                    credential=self.credential
                )

                replies = result.get('replies', [])

                if not replies:
                    print(f"  本页无评论")
                    continue

                # 处理每条评论
                for reply in replies:
                    comment_data = self._parse_comment(reply, bvid)
                    self.all_comments.append(comment_data)

                    # 如果有二级评论，获取它们
                    rcount = reply.get('rcount', 0)
                    if rcount > 0:
                        sub_comments = await self._fetch_sub_comments(
                            aid, reply.get('rpid'), bvid
                        )
                        self.all_comments.extend(sub_comments)

                print(f"  获取到 {len(replies)} 条一级评论")

                await asyncio.sleep(0.3)  # 避免请求过快

            except Exception as e:
                print(f"  ❌ 获取失败: {e}")
                continue

        print(f"\n✅ 获取完成！共 {len(self.all_comments)} 条评论（含二级评论）")

        return self.all_comments

    async def _fetch_sub_comments(
        self,
        aid: int,
        root_rpid: int,
        bvid: str
    ) -> list:
        """获取二级评论"""
        try:
            # 使用 Comment 对象获取子评论
            parent_comment = comment.Comment(
                rpid=root_rpid,
                type_=comment.CommentResourceType.VIDEO,
                oid=aid,
                credential=self.credential
            )

            result = await parent_comment.get_sub_comments(page_index=1, page_size=20)

            sub_replies = result.get('replies', [])
            sub_comments = []

            for sub in sub_replies:
                comment_data = self._parse_comment(sub, bvid, is_reply=True)
                sub_comments.append(comment_data)

            return sub_comments

        except Exception as e:
            print(f"    ⚠️ 获取二级评论失败: {e}")
            return []

    def _parse_comment(self, reply: dict, bvid: str, is_reply: bool = False) -> dict:
        """解析评论数据"""
        member = reply.get('member', {})
        content_obj = reply.get('content', {})
        reply_control = reply.get('reply_control', {})

        # 提取表情和跳转链接（增加安全检查）
        emotes = []
        jump_urls = []

        # 检查 emote 字段
        emote_data = content_obj.get('emote')
        if emote_data:
            if isinstance(emote_data, dict):
                for emote in emote_data.values():
                    if isinstance(emote, dict):
                        emotes.append({
                            'text': emote.get('text', ''),
                            'url': emote.get('url', '')
                        })
            elif isinstance(emote_data, list):
                for emote in emote_data:
                    if isinstance(emote, dict):
                        emotes.append({
                            'text': emote.get('text', ''),
                            'url': emote.get('url', '')
                        })

        # 检查 jump_url 字段
        jump_data = content_obj.get('jump_url')
        if jump_data:
            if isinstance(jump_data, list):
                for jump in jump_data:
                    if isinstance(jump, dict):
                        jump_urls.append({
                            'title': jump.get('title', ''),
                            'url': jump.get('pc_url', '')
                        })

        # 安全获取用户等级
        level_info = member.get('level_info')
        if isinstance(level_info, dict):
            level = level_info.get('current_level')
        else:
            level = level_info if level_info else None

        return {
            'bvid': bvid,
            'rpid': reply.get('rpid'),
            'parent_rpid': reply.get('parent', None),
            'root_rpid': reply.get('root', None),
            'is_reply': is_reply,

            # 用户信息
            'user': {
                'mid': member.get('mid'),
                'name': member.get('uname'),
                'avatar': member.get('avatar'),
                'level': level
            },

            # 评论内容
            'content': {
                'message': content_obj.get('message', ''),
                'emotes': emotes,
                'jump_urls': jump_urls
            },

            # 统计信息
            'like': reply.get('like', 0),
            'reply_count': reply.get('rcount', 0),

            # 时间信息
            'ctime': reply.get('ctime'),
            'ctime_formatted': datetime.fromtimestamp(reply.get('ctime', 0)).strftime('%Y-%m-%d %H:%M:%S'),
            'time_desc': reply_control.get('time_desc', '') if isinstance(reply_control, dict) else '',

            # 其他
            'up_action': reply.get('up_action', {}),
            'invisible': reply.get('invisible', False)
        }

    def print_summary(self):
        """打印评论摘要"""
        if not self.all_comments:
            print("\n❌ 暂无评论")
            return

        top_level = [c for c in self.all_comments if not c['is_reply']]
        replies = [c for c in self.all_comments if c['is_reply']]

        print(f"\n📊 评论统计:")
        print(f"  总评论数: {len(self.all_comments)}")
        print(f"  一级评论: {len(top_level)}")
        print(f"  二级评论: {len(replies)}")

        # 显示点赞最多的评论
        top_liked = sorted(top_level, key=lambda x: x['like'], reverse=True)[:3]
        print(f"\n🔥 最受欢迎的评论:")
        for idx, cmt in enumerate(top_liked, 1):
            print(f"\n  {idx}. @{cmt['user']['name']} ({cmt['like']}赞, {cmt['reply_count']}回复)")
            content = cmt['content']['message']
            if len(content) > 50:
                content = content[:50] + "..."
            print(f"     {content}")

    def save_json(self, filename: str = None) -> str:
        """保存为JSON"""
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

        print(f"\n💾 JSON 已保存: {filepath}")
        return str(filepath)

    def save_markdown(self, filename: str = None) -> str:
        """保存为Markdown"""
        if filename is None:
            filename = f"comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        filepath = self.output_dir / filename

        md_lines = [
            "# 视频评论报告\n",
            f"**获取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**评论总数**: {len(self.all_comments)}\n",
            "\n---\n"
        ]

        # 按一级评论分组
        current_root = None
        for cmt in self.all_comments:
            if not cmt['is_reply']:
                # 一级评论
                if current_root is not None:
                    md_lines.append("\n---\n")

                current_root = cmt

                md_lines.extend([
                    f"## @{cmt['user']['name']} ({cmt['like']}赞)\n",
                    f"\n{cmt['content']['message']}\n",
                    f"\n*{cmt['time_desc']} · {cmt['reply_count']}条回复*\n"
                ])

                # 如果有表情
                if cmt['content']['emotes']:
                    md_lines.append(f"\n**表情**: {', '.join([e['text'] for e in cmt['content']['emotes']])}\n")
            else:
                # 二级评论
                md_lines.extend([
                    f"\n### 💬 @{cmt['user']['name']}\n",
                    f"{cmt['content']['message']}\n",
                    f"\n*{cmt['time_desc']} · {cmt['like']}赞*\n"
                ])

        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(md_lines)

        print(f"📝 Markdown 已保存: {filepath}")
        return str(filepath)


async def main():
    """主函数"""
    import sys

    # 从命令行获取BVID
    if len(sys.argv) > 1:
        bvid = sys.argv[1]
    else:
        bvid = input("请输入视频BVID: ").strip()

    # 获取最大页数（可选）
    max_pages = None
    if len(sys.argv) > 2:
        try:
            max_pages = int(sys.argv[2])
        except:
            pass

    # 创建获取器
    fetcher = CommentFetcher()

    # 获取评论
    await fetcher.fetch_video_comments(bvid, max_pages=max_pages)

    # 打印摘要
    fetcher.print_summary()

    # 保存结果
    fetcher.save_json()
    fetcher.save_markdown()

    print("\n🎉 完成！")


if __name__ == "__main__":
    asyncio.run(main())
