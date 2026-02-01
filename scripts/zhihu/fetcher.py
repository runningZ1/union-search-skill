"""
知乎搜索模块 - 完整内容获取器

获取知乎回答、文章的完整内容和评论数据
"""
import asyncio
from typing import Dict, Any, Optional, List

from loguru import logger

from .client import ZhihuAPIClient
from .field import ContentType
from .exception import ZhihuNetworkError


class ZhihuContentFetcher:
    """知乎完整内容获取器

    获取回答、文章的完整内容和评论数据
    """

    def __init__(self, api_client: ZhihuAPIClient):
        """初始化内容获取器

        Args:
            api_client: 知乎 API 客户端实例
        """
        self.api_client = api_client

    async def fetch_full_content(
        self,
        item: Dict[str, Any],
        include_comments: bool = False,
        comments_limit: int = 20,
    ) -> Dict[str, Any]:
        """获取完整内容

        根据内容类型调用对应的详情接口

        Args:
            item: 搜索结果项（必须包含 type 和 id 字段）
            include_comments: 是否包含评论
            comments_limit: 评论数量限制

        Returns:
            包含完整内容的结果字典
        """
        content_type = item.get("type")
        content_id = item.get("id")

        if not content_type or not content_id:
            logger.warning(f"跳过无效项: type={content_type}, id={content_id}")
            return item

        # 复制原始数据
        result = item.copy()

        try:
            if content_type == ContentType.ANSWER.value:
                # 获取回答详情
                detail = await self.fetch_answer_detail(content_id)
                result.update({
                    "content": detail.get("content", ""),
                    "full_content": detail.get("content", ""),
                })

                # 获取评论
                if include_comments:
                    question_id = item.get("question", {}).get("id")
                    if question_id:
                        comments = await self.fetch_comments(
                            question_id, content_id, comments_limit
                        )
                        result["comments_data"] = comments

            elif content_type == ContentType.ARTICLE.value:
                # 获取文章详情
                detail = await self.fetch_article_detail(content_id)
                result.update({
                    "content": detail.get("content", ""),
                    "full_content": detail.get("content", ""),
                })

                # 文章评论接口不同，暂不实现
                if include_comments:
                    logger.debug("文章评论暂不支持")

            elif content_type == ContentType.QUESTION.value:
                # 获取问题详情
                detail = await self.fetch_question_detail(content_id)
                result.update({
                    "detail": detail.get("detail", ""),
                    "answer_count": detail.get("answer_count", 0),
                })

            # 添加延迟避免请求过快
            await asyncio.sleep(0.5)

        except ZhihuNetworkError as e:
            logger.warning(f"获取完整内容失败 (id={content_id}): {e}")
        except Exception as e:
            logger.warning(f"处理内容时发生错误 (id={content_id}): {e}")

        return result

    async def fetch_answer_detail(self, answer_id: str) -> Dict[str, Any]:
        """获取回答完整内容

        Args:
            answer_id: 回答 ID

        Returns:
            回答详情数据
        """
        logger.debug(f"获取回答详情: {answer_id}")
        response = await self.api_client.get_answer_detail(answer_id)

        return {
            "id": response.get("id", ""),
            "content": response.get("content", ""),
            "excerpt": response.get("excerpt", ""),
            "author": response.get("author", {}),
            "voteup_count": response.get("voteup_count", 0),
            "comment_count": response.get("comment_count", 0),
            "created_time": response.get("created_time"),
            "updated_time": response.get("updated_time"),
        }

    async def fetch_article_detail(self, article_id: str) -> Dict[str, Any]:
        """获取文章完整内容

        Args:
            article_id: 文章 ID

        Returns:
            文章详情数据
        """
        logger.debug(f"获取文章详情: {article_id}")
        response = await self.api_client.get_article_detail(article_id)

        return {
            "id": response.get("id", ""),
            "title": response.get("title", ""),
            "content": response.get("content", ""),
            "excerpt": response.get("excerpt", ""),
            "author": response.get("author", {}),
            "voteup_count": response.get("voteup_count", 0),
            "comment_count": response.get("comment_count", 0),
            "read_count": response.get("read_count", 0),
            "topics": [t.get("name") for t in response.get("topics", [])],
            "created": response.get("created"),
            "modified": response.get("modified"),
        }

    async def fetch_question_detail(self, question_id: str) -> Dict[str, Any]:
        """获取问题详情

        Args:
            question_id: 问题 ID

        Returns:
            问题详情数据
        """
        logger.debug(f"获取问题详情: {question_id}")
        response = await self.api_client.get_question_detail(question_id)

        return {
            "id": response.get("id", ""),
            "title": response.get("title", ""),
            "detail": response.get("detail", ""),
            "excerpt": response.get("excerpt", ""),
            "answer_count": response.get("answer_count", 0),
            "follower_count": response.get("follower_count", 0),
            "visit_count": response.get("visit_count", 0),
            "topics": [t.get("name") for t in response.get("topics", [])],
            "created": response.get("created"),
            "updated_time": response.get("updated_time"),
        }

    async def fetch_comments(
        self,
        question_id: str,
        answer_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """获取评论列表

        Args:
            question_id: 问题 ID
            answer_id: 回答 ID
            limit: 每页数量
            offset: 偏移量

        Returns:
            评论列表
        """
        logger.debug(f"获取评论: question={question_id}, answer={answer_id}")

        try:
            response = await self.api_client.get_comments(
                question_id=question_id,
                answer_id=answer_id,
                limit=limit,
                offset=offset,
            )

            # 解析评论数据
            comments = []
            for comment in response.get("data", []):
                comments.append({
                    "id": comment.get("id", ""),
                    "content": comment.get("content", ""),
                    "author": {
                        "id": comment.get("author", {}).get("id", ""),
                        "name": comment.get("author", {}).get("name", ""),
                    },
                    "voteup_count": comment.get("voteup_count", 0),
                    "created_time": comment.get("created_time"),
                })

            return comments

        except ZhihuNetworkError as e:
            logger.warning(f"获取评论失败: {e}")
            return []

    async def fetch_batch_full_content(
        self,
        items: List[Dict[str, Any]],
        include_comments: bool = False,
        comments_limit: int = 20,
        max_concurrent: int = 3,
    ) -> List[Dict[str, Any]]:
        """批量获取完整内容

        Args:
            items: 搜索结果列表
            include_comments: 是否包含评论
            comments_limit: 评论数量限制
            max_concurrent: 最大并发数

        Returns:
            包含完整内容的结果列表
        """
        logger.info(f"批量获取完整内容: {len(items)} 项, 并发数={max_concurrent}")

        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_semaphore(item):
            async with semaphore:
                return await self.fetch_full_content(
                    item,
                    include_comments=include_comments,
                    comments_limit=comments_limit,
                )

        # 并发获取
        tasks = [fetch_with_semaphore(item) for item in items]
        results = await asyncio.gather(*tasks)

        logger.info(f"批量获取完成: {len(results)} 项")
        return results


# 便捷函数
async def enrich_with_full_content(
    items: List[Dict[str, Any]],
    api_client: ZhihuAPIClient,
    include_comments: bool = False,
) -> List[Dict[str, Any]]:
    """为搜索结果添加完整内容

    Args:
        items: 搜索结果列表
        api_client: API 客户端
        include_comments: 是否包含评论

    Returns:
        包含完整内容的结果列表
    """
    fetcher = ZhihuContentFetcher(api_client)
    return await fetcher.fetch_batch_full_content(
        items,
        include_comments=include_comments,
    )
