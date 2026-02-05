"""
评论API测试脚本
用于研究和测试B站评论API的各种功能
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from bilibili_api import comment, video, Credential


async def test_basic_comment_api():
    """测试基础评论API（无需登录）"""
    print("=" * 60)
    print("测试1: 基础评论API（无需登录）")
    print("=" * 60)

    bvid = "BV19CzjBvEGx"
    v = video.Video(bvid=bvid)
    info = await v.get_info()
    aid = info.get("aid")

    print(f"\n视频信息:")
    print(f"  BVID: {bvid}")
    print(f"  AV号: {aid}")
    print(f"  标题: {info.get('title')}")
    print(f"  评论数: {info.get('stat', {}).get('reply', 0)}")

    # 尝试获取评论
    print("\n尝试获取评论...")
    try:
        result = await comment.get_comments(
            oid=aid,
            type_=comment.CommentResourceType.VIDEO,
            page_index=1
        )
        print(f"\nAPI返回结果:")
        print(f"  page.num: {result.get('page', {}).get('num')}")
        print(f"  page.size: {result.get('page', {}).get('size')}")
        print(f"  page.count: {result.get('page', {}).get('count')}")
        print(f"  replies: {result.get('replies')}")
        print(f"  其他键: {list(result.keys())}")

        # 保存完整响应
        output_file = Path("output") / "test_basic_comment_response.json"
        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n完整响应已保存到: {output_file}")

    except Exception as e:
        print(f"错误: {e}")


async def test_comment_with_credential(sessdata: str):
    """测试带登录凭证的评论API"""
    print("\n" + "=" * 60)
    print("测试2: 带登录凭证的评论API")
    print("=" * 60)

    try:
        credential = Credential(sessdata=sessdata)
        print("✅ 凭证创建成功")
    except Exception as e:
        print(f"❌ 凭证创建失败: {e}")
        return

    bvid = "BV19CzjBvEGx"
    v = video.Video(bvid=bvid, credential=credential)
    info = await v.get_info()
    aid = info.get("aid")

    print(f"\n视频信息:")
    print(f"  BVID: {bvid}")
    print(f"  评论数: {info.get('stat', {}).get('reply', 0)}")

    # 尝试获取评论
    print("\n尝试获取评论...")
    try:
        result = await comment.get_comments(
            oid=aid,
            type_=comment.CommentResourceType.VIDEO,
            page_index=1,
            credential=credential
        )

        count = result.get('page', {}).get('count', 0)
        replies = result.get('replies', [])

        print(f"\n✅ 成功获取评论!")
        print(f"  总评论数: {count}")
        print(f"  本页评论数: {len(replies) if replies else 0}")

        if replies:
            print(f"\n前3条评论:")
            for idx, reply in enumerate(replies[:3], 1):
                member = reply.get('member', {})
                content = reply.get('content', {}).get('message', '')
                like = reply.get('like', 0)

                print(f"\n  {idx}. @{member.get('uname', '匿名')} ({like}赞)")
                print(f"     {content[:100]}..." if len(content) > 100 else f"     {content}")

        # 保存完整响应
        output_file = Path("output") / "test_auth_comment_response.json"
        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n完整响应已保存到: {output_file}")

    except Exception as e:
        print(f"❌ 获取评论失败: {e}")


async def test_comment_pagination(sessdata: str):
    """测试评论翻页"""
    print("\n" + "=" * 60)
    print("测试3: 评论翻页")
    print("=" * 60)

    credential = Credential(sessdata=sessdata)

    bvid = "BV19CzjBvEGx"
    v = video.Video(bvid=bvid, credential=credential)
    info = await v.get_info()
    aid = info.get("aid")

    total_count = info.get('stat', {}).get('reply', 0)
    page_size = 20
    total_pages = (total_count + page_size - 1) // page_size

    print(f"\n视频评论总数: {total_count}")
    print(f"预计页数: {total_pages}")

    all_comments = []

    # 获取前3页作为测试
    for page_num in range(1, min(4, total_pages + 1)):
        try:
            result = await comment.get_comments(
                oid=aid,
                type_=comment.CommentResourceType.VIDEO,
                page_index=page_num,
                credential=credential
            )

            replies = result.get('replies', [])
            if replies:
                for reply in replies:
                    member = reply.get('member', {})
                    content = reply.get('content', {}).get('message', '')

                    all_comments.append({
                        'user': member.get('uname', '匿名'),
                        'user_id': member.get('mid', ''),
                        'content': content,
                        'like': reply.get('like', 0),
                        'reply_count': reply.get('rcount', 0),
                        'ctime': reply.get('ctime', 0)
                    })

                print(f"  第{page_num}页: 获取到 {len(replies)} 条评论")
            else:
                print(f"  第{page_num}页: 无评论")

            await asyncio.sleep(0.3)  # 避免请求过快

        except Exception as e:
            print(f"  第{page_num}页获取失败: {e}")

    print(f"\n总共获取: {len(all_comments)} 条评论")

    # 保存结果
    output_file = Path("output") / "test_comments_pagination.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            'bvid': bvid,
            'fetch_time': datetime.now().isoformat(),
            'total_fetched': len(all_comments),
            'comments': all_comments
        }, f, ensure_ascii=False, indent=2)
    print(f"结果已保存到: {output_file}")


async def test_comment_ordering(sessdata: str):
    """测试评论排序方式"""
    print("\n" + "=" * 60)
    print("测试4: 评论排序方式")
    print("=" * 60)

    credential = Credential(sessdata=sessdata)

    bvid = "BV19CzjBvEGx"
    v = video.Video(bvid=bvid, credential=credential)
    info = await v.get_info()
    aid = info.get("aid")

    # 测试两种排序方式
    for order_type, order_name in [
        (comment.OrderType.TIME, "按时间"),
        (comment.OrderType.LIKE, "按点赞"),
        (comment.OrderType.HOT, "按热度")
    ]:
        print(f"\n{order_name}排序:")
        try:
            result = await comment.get_comments(
                oid=aid,
                type_=comment.CommentResourceType.VIDEO,
                page_index=1,
                order=order_type,
                credential=credential
            )

            replies = result.get('replies', [])
            if replies:
                print(f"  成功! 获取到 {len(replies)} 条评论")
                print(f"  第1条: {replies[0].get('content', {}).get('message', '')[:50]}...")
            else:
                print(f"  成功! 但无评论")

        except Exception as e:
            print(f"  失败: {e}")


async def test_subcomments(sessdata: str):
    """测试二级评论（楼中楼）"""
    print("\n" + "=" * 60)
    print("测试5: 二级评论")
    print("=" * 60)

    credential = Credential(sessdata=sessdata)

    bvid = "BV19CzjBvEGx"
    v = video.Video(bvid=bvid, credential=credential)
    info = await v.get_info()
    aid = info.get("aid")

    # 先获取一级评论
    result = await comment.get_comments(
        oid=aid,
        type_=comment.CommentResourceType.VIDEO,
        page_index=1,
        credential=credential
    )

    replies = result.get('replies', [])

    if not replies:
        print("没有评论可供测试二级评论")
        return

    # 找一个有回复的评论
    for reply in replies:
        rcount = reply.get('rcount', 0)
        if rcount > 0:
            rpid = reply.get('rpid')
            print(f"\n找到一个有 {rcount} 条回复的评论")
            print(f"评论内容: {reply.get('content', {}).get('message', '')[:50]}...")

            # 获取二级评论
            try:
                sub_result = await comment.get_comments(
                    oid=aid,
                    type_=comment.CommentResourceType.VIDEO,
                    page_index=1,
                    root=rpid,
                    credential=credential
                )

                sub_replies = sub_result.get('replies', [])
                print(f"\n二级评论:")
                for idx, sub in enumerate(sub_replies[:5], 1):
                    member = sub.get('member', {})
                    content = sub.get('content', {}).get('message', '')
                    print(f"  {idx}. @{member.get('uname', '匿名')}")
                    print(f"     {content[:100]}...")

                break
            except Exception as e:
                print(f"获取二级评论失败: {e}")
                break

    if all(r.get('rcount', 0) == 0 for r in replies):
        print("第一页评论中没有二级评论")


async def main():
    """主函数"""
    print("🔍 B站评论API测试")
    print("=" * 60)

    # 测试1: 无需登录的API
    await test_basic_comment_api()

    # 询问是否进行登录测试
    print("\n" + "=" * 60)
    sessdata = input("\n要进行登录测试，请输入SESSDATA（按Enter跳过）: ").strip()

    if not sessdata:
        print("\n⚠️ 跳过登录测试，只能测试基础API")
        return

    # 测试2-5: 需要登录的API
    await test_comment_with_credential(sessdata)
    await test_comment_pagination(sessdata)
    await test_comment_ordering(sessdata)
    await test_subcomments(sessdata)

    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
