"""
知乎搜索模块 - 数据提取器

从知乎 API 响应中提取结构化数据
"""
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

from .field import ContentType
from .exception import ZhihuParseError


class ZhihuExtractor:
    """知乎数据提取器

    从知乎 API 响应中提取标准化的数据结构
    """

    @staticmethod
    def extract_search_result(item: Dict[str, Any], rank: int = 0) -> Dict[str, Any]:
        """从搜索结果 API 响应提取单条结果

        Args:
            item: API 返回的单条搜索结果数据
            rank: 结果排名

        Returns:
            标准化的搜索结果字典

        Raises:
            ZhihuParseError: 数据解析失败
        """
        try:
            # 获取实际的对象数据
            obj = item.get("object", item)

            # 确定内容类型
            content_type = obj.get("type", "")
            if content_type == "answer":
                return ZhihuExtractor._extract_answer(obj, rank)
            elif content_type == "article":
                return ZhihuExtractor._extract_article(obj, rank)
            elif content_type == "question":
                return ZhihuExtractor._extract_question(obj, rank)
            else:
                # 未知类型，尝试通用提取
                return ZhihuExtractor._extract_generic(obj, rank)

        except Exception as e:
            raise ZhihuParseError(f"解析搜索结果失败: {e}") from e

    @staticmethod
    def _extract_answer(obj: Dict[str, Any], rank: int) -> Dict[str, Any]:
        """提取回答类型的数据"""
        author = obj.get("author", {})
        question = obj.get("question", {})

        return {
            "rank": rank,
            "id": obj.get("id", ""),
            "type": ContentType.ANSWER.value,
            "title": question.get("title", ""),
            "excerpt": obj.get("excerpt", "")[:200] if obj.get("excerpt") else "",
            "author": ZhihuExtractor._extract_author(author),
            "url": f"https://www.zhihu.com/question/{question.get('id', '')}/answer/{obj.get('id', '')}",
            "stats": {
                "votes": obj.get("voteup_count", 0),
                "comments": obj.get("comment_count", 0),
                "views": None,  # 知乎不公开浏览量
            },
            "created_at": ZhihuExtractor._timestamp_to_date(obj.get("created_time")),
            "updated_at": ZhihuExtractor._timestamp_to_date(obj.get("updated_time")),
            "question": {
                "id": question.get("id", ""),
                "title": question.get("title", ""),
            },
            "topics": ZhihuExtractor._extract_topics(obj.get("topics", [])),
        }

    @staticmethod
    def _extract_article(obj: Dict[str, Any], rank: int) -> Dict[str, Any]:
        """提取文章类型的数据"""
        author = obj.get("author", {})

        return {
            "rank": rank,
            "id": obj.get("id", ""),
            "type": ContentType.ARTICLE.value,
            "title": obj.get("title", ""),
            "excerpt": obj.get("excerpt", "")[:200] if obj.get("excerpt") else "",
            "author": ZhihuExtractor._extract_author(author),
            "url": f"https://zhuanlan.zhihu.com/p/{obj.get('id', '')}",
            "stats": {
                "votes": obj.get("voteup_count", 0),
                "comments": obj.get("comment_count", 0),
                "views": obj.get("read_count", None),  # 文章可能有阅读量
            },
            "created_at": ZhihuExtractor._timestamp_to_date(obj.get("created")),
            "updated_at": ZhihuExtractor._timestamp_to_date(obj.get("modified", obj.get("updated"))),
            "question": None,
            "topics": ZhihuExtractor._extract_topics(obj.get("topics", [])),
        }

    @staticmethod
    def _extract_question(obj: Dict[str, Any], rank: int) -> Dict[str, Any]:
        """提取问题类型的数据"""
        author = obj.get("author", {})

        return {
            "rank": rank,
            "id": obj.get("id", ""),
            "type": ContentType.QUESTION.value,
            "title": obj.get("title", ""),
            "excerpt": obj.get("excerpt", "")[:200] if obj.get("excerpt") else "",
            "author": ZhihuExtractor._extract_author(author),
            "url": f"https://www.zhihu.com/question/{obj.get('id', '')}",
            "stats": {
                "votes": obj.get("voteup_count", 0),
                "comments": obj.get("comment_count", 0),
                "views": None,
                "followers": obj.get("follower_count", 0),  # 问题关注者数
            },
            "created_at": ZhihuExtractor._timestamp_to_date(obj.get("created")),
            "updated_at": ZhihuExtractor._timestamp_to_date(obj.get("updated_time")),
            "question": {
                "id": obj.get("id", ""),
                "title": obj.get("title", ""),
            },
            "topics": ZhihuExtractor._extract_topics(obj.get("topics", [])),
        }

    @staticmethod
    def _extract_generic(obj: Dict[str, Any], rank: int) -> Dict[str, Any]:
        """通用数据提取（用于未知类型）"""
        return {
            "rank": rank,
            "id": obj.get("id", ""),
            "type": obj.get("type", "unknown"),
            "title": obj.get("title", ""),
            "excerpt": str(obj.get("excerpt", ""))[:200],
            "author": ZhihuExtractor._extract_author(obj.get("author", {})),
            "url": obj.get("url", ""),
            "stats": {},
            "created_at": None,
            "updated_at": None,
            "question": None,
            "topics": [],
        }

    @staticmethod
    def _extract_author(author_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取作者信息"""
        if not author_data:
            return {
                "id": "",
                "name": "匿名用户",
                "url": "",
            }

        url_token = author_data.get("url_token", "")
        return {
            "id": author_data.get("id", ""),
            "name": author_data.get("name", ""),
            "url": f"https://www.zhihu.com/people/{url_token}" if url_token else "",
            "avatar": author_data.get("avatar_url", ""),
            "headline": author_data.get("headline", ""),
        }

    @staticmethod
    def _extract_topics(topics_data: List[Dict[str, Any]]) -> List[str]:
        """提取话题标签"""
        if not topics_data:
            return []

        topics = []
        for topic in topics_data:
            if isinstance(topic, dict):
                name = topic.get("name", "")
                if name:
                    topics.append(name)
            elif isinstance(topic, str):
                topics.append(topic)

        return topics[:5]  # 最多返回 5 个话题

    @staticmethod
    def _timestamp_to_date(timestamp: Optional[int]) -> Optional[str]:
        """将时间戳转换为日期字符串

        Args:
            timestamp: Unix 时间戳（秒）

        Returns:
            格式化的日期字符串 (YYYY-MM-DD)，如果输入无效则返回 None
        """
        if not timestamp:
            return None

        try:
            # 知乎时间戳可能是秒或毫秒
            if timestamp > 10000000000:  # 毫秒
                timestamp = timestamp / 1000

            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d")

        except (ValueError, OSError, OverflowError):
            return None

    @staticmethod
    def extract_search_results(
        items: List[Dict[str, Any]],
        start_rank: int = 1
    ) -> List[Dict[str, Any]]:
        """批量提取搜索结果

        Args:
            items: API 返回的搜索结果列表
            start_rank: 起始排名

        Returns:
            标准化的搜索结果列表
        """
        results = []
        for i, item in enumerate(items):
            try:
                result = ZhihuExtractor.extract_search_result(item, rank=start_rank + i)
                results.append(result)
            except ZhihuParseError as e:
                # 跳过解析失败的单条结果，继续处理其他结果
                import logging
                logging.warning(f"跳过解析失败的结果: {e}")
                continue

        return results
