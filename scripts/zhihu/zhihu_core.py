"""
知乎搜索核心模块 - 集成版本
整合了所有功能到单一文件，提供完整的知乎搜索能力

基于 TikHub API 实现
作者: Claude
日期: 2026-02-20
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

import requests
from loguru import logger
from dotenv import load_dotenv


# ============================================================================
# 枚举定义
# ============================================================================

class SearchType(Enum):
    """搜索类型枚举"""
    GENERAL = "general"
    PEOPLE = "people"
    TOPIC = "topic"
    COLUMN = "column"
    LIVE = "live"
    ALBUM = "album"
    ARTICLE = "article"


class TimeInterval(Enum):
    """时间筛选枚举"""
    ALL = ""
    ONE_DAY = "a_day"
    ONE_WEEK = "a_week"
    ONE_MONTH = "a_month"
    THREE_MONTHS = "three_months"
    HALF_YEAR = "half_a_year"
    ONE_YEAR = "a_year"


class SearchSource(Enum):
    """搜索来源枚举"""
    NORMAL = "Normal"
    FILTER = "Filter"


class Vertical(Enum):
    """内容类型筛选"""
    ALL = ""
    ANSWER = "answer"
    ARTICLE = "article"
    ZVIDEO = "zvideo"


class SortType(Enum):
    """排序方式"""
    DEFAULT = ""
    UPVOTED = "upvoted_count"
    NEWEST = "created_time"


class ShowAllTopics(Enum):
    """是否显示话题"""
    HIDE = "0"
    SHOW = "1"


# ============================================================================
# 数据提取器
# ============================================================================

class ZhihuExtractor:
    """知乎搜索结果数据提取器"""

    @staticmethod
    def extract_item(item: Dict[str, Any]) -> Dict[str, Any]:
        """提取单个搜索结果的关键信息"""
        try:
            item_type = item.get("type", "unknown")
            obj = item.get("object", {})
            highlight = item.get("highlight") or {}

            extracted = {
                "type": obj.get("type", item_type),
                "id": obj.get("id") or obj.get("original_id"),
                "title": highlight.get("title") or obj.get("title", "") or obj.get("name", ""),
                "excerpt": highlight.get("description") or obj.get("excerpt", ""),
                "url": obj.get("url", ""),
                "created_time": obj.get("created_time"),
            }

            author = obj.get("author", {})
            if author:
                extracted["author"] = {
                    "name": author.get("name", ""),
                    "url_token": author.get("url_token", ""),
                    "avatar_url": author.get("avatar_url", ""),
                    "headline": author.get("headline", ""),
                }

            extracted["stats"] = {
                "voteup_count": obj.get("voteup_count", 0),
                "comment_count": obj.get("comment_count", 0),
                "favorite_count": obj.get("favorites_count", 0),
            }

            obj_type = obj.get("type", "")
            if obj_type == "answer":
                question = obj.get("question", {})
                if question:
                    extracted["question"] = {
                        "id": question.get("id"),
                        "title": question.get("title"),
                        "url": question.get("url"),
                    }
            elif obj_type == "article":
                extracted["column"] = obj.get("column", {})
            elif obj_type == "topic":
                extracted["followers_count"] = obj.get("followers_count", 0)
                extracted["questions_count"] = obj.get("questions_count", 0)

            return extracted

        except Exception as e:
            logger.warning(f"提取数据时出错: {e}")
            return {"type": "error", "error": str(e)}

    @staticmethod
    def extract_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量提取搜索结果"""
        return [ZhihuExtractor.extract_item(item) for item in items]


# ============================================================================
# API 客户端
# ============================================================================

class ZhihuAPIClient:
    """知乎搜索 API 客户端（基于 TikHub）"""

    BASE_URL = "https://api.tikhub.io"
    SEARCH_ENDPOINT = "/api/v1/zhihu/web/fetch_article_search_v3"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3

    def __init__(self, api_token: Optional[str] = None):
        """初始化客户端"""
        if api_token is None:
            project_root = Path(__file__).parent.parent.parent
            env_file = project_root / ".env"
            if env_file.exists():
                load_dotenv(env_file)
            api_token = os.getenv("TIKHUB_TOKEN")

        if not api_token:
            raise ValueError("未找到 TIKHUB_TOKEN，请在 .env 文件中配置")

        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        })

    def search(
        self,
        keyword: str,
        offset: int = 0,
        limit: int = 20,
        show_all_topics: ShowAllTopics = ShowAllTopics.HIDE,
        search_source: SearchSource = SearchSource.NORMAL,
        search_hash_id: str = "",
        vertical: Vertical = Vertical.ALL,
        sort: SortType = SortType.DEFAULT,
        time_interval: TimeInterval = TimeInterval.ALL,
        vertical_info: str = "0,0,0,0,0,0,0,0,0,0,0,0"
    ) -> Dict[str, Any]:
        """执行搜索"""
        url = f"{self.BASE_URL}{self.SEARCH_ENDPOINT}"

        params = {
            "keyword": keyword,
            "offset": offset,
            "limit": min(limit, 100),
            "show_all_topics": show_all_topics.value,
            "search_source": search_source.value,
            "vertical": vertical.value,
            "sort": sort.value,
            "time_interval": time_interval.value,
            "vertical_info": vertical_info,
        }

        if search_hash_id:
            params["search_hash_id"] = search_hash_id

        logger.info(f"搜索知乎: keyword={keyword}, offset={offset}, limit={limit}")

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(url, params=params, timeout=self.DEFAULT_TIMEOUT)
                response.raise_for_status()

                data = response.json()

                if data.get("code") != 200:
                    logger.error(f"API 返回错误: {data.get('message')}")
                    return {"code": data.get("code"), "message": data.get("message"), "data": None}

                result_data = data.get("data", {})
                items = result_data.get("data", [])

                logger.success(f"搜索成功，返回 {len(items)} 条结果")

                return {
                    "code": 200,
                    "message": "success",
                    "data": {
                        "items": items,
                        "has_more": not result_data.get("paging", {}).get("is_end", True),
                        "total": len(items)
                    }
                }

            except requests.exceptions.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.MAX_RETRIES}): {e}")
                    continue
                else:
                    logger.error(f"请求失败: {e}")
                    return {"code": -1, "message": str(e), "data": None}

        return {"code": -1, "message": "达到最大重试次数", "data": None}


# ============================================================================
# 核心搜索类
# ============================================================================

class ZhihuSearchCore:
    """知乎搜索核心类 - 提供完整的搜索功能"""

    def __init__(self, api_token: Optional[str] = None):
        """初始化核心搜索类"""
        self.client = ZhihuAPIClient(api_token)
        self.extractor = ZhihuExtractor()

    def search(
        self,
        keyword: str,
        limit: int = 20,
        vertical: Vertical = Vertical.ALL,
        sort: SortType = SortType.DEFAULT,
        time_interval: TimeInterval = TimeInterval.ALL,
        show_all_topics: ShowAllTopics = ShowAllTopics.HIDE,
        search_source: SearchSource = SearchSource.NORMAL,
        save_response: bool = False,
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        执行知乎搜索
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量
            vertical: 内容类型筛选
            sort: 排序方式
            time_interval: 时间筛选
            show_all_topics: 是否显示话题
            search_source: 搜索来源
            save_response: 是否保存响应
            output_dir: 输出目录
            
        Returns:
            提取后的搜索结果列表
        """
        try:
            # 执行搜索
            result = self.client.search(
                keyword=keyword,
                offset=0,
                limit=limit,
                show_all_topics=show_all_topics,
                search_source=search_source,
                vertical=vertical,
                sort=sort,
                time_interval=time_interval
            )

            if result.get("code") != 200:
                logger.error(f"搜索失败: {result.get('message')}")
                return []

            # 提取数据
            items = result.get("data", {}).get("items", [])
            if not items:
                logger.warning("未找到任何结果")
                return []

            extracted_items = self.extractor.extract_items(items)

            # 保存响应
            if save_response:
                self._save_response(result, keyword, output_dir)

            logger.success(f"成功获取 {len(extracted_items)} 条结果")
            return extracted_items

        except Exception as e:
            logger.error(f"搜索过程中出错: {e}")
            return []

    def _save_response(
        self,
        response_data: dict,
        keyword: str,
        output_dir: Optional[str] = None
    ):
        """保存API响应到文件"""
        try:
            if output_dir is None:
                output_dir = Path(__file__).parent / "responses"
            else:
                output_dir = Path(output_dir)

            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{keyword}_{timestamp}.json"
            filepath = output_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)

            logger.success(f"响应已保存: {filepath}")

        except Exception as e:
            logger.warning(f"保存响应失败: {e}")


# ============================================================================
# 命令行接口
# ============================================================================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="知乎搜索核心模块")
    parser.add_argument("keyword", help="搜索关键词")
    parser.add_argument("-n", "--num", type=int, default=20, help="结果数量")
    parser.add_argument(
        "-v", "--vertical",
        default="all",
        choices=["all", "answer", "article", "zvideo"],
        help="内容类型"
    )
    parser.add_argument(
        "-s", "--sort",
        default="default",
        choices=["default", "upvoted", "newest"],
        help="排序方式"
    )
    parser.add_argument(
        "-t", "--time",
        default="all",
        choices=["all", "day", "week", "month", "3months", "6months", "year"],
        help="时间筛选"
    )
    parser.add_argument("--save", action="store_true", help="保存响应")
    parser.add_argument("-o", "--output", help="输出目录")

    args = parser.parse_args()

    # 映射参数
    vertical_map = {
        "all": Vertical.ALL,
        "answer": Vertical.ANSWER,
        "article": Vertical.ARTICLE,
        "zvideo": Vertical.ZVIDEO
    }

    sort_map = {
        "default": SortType.DEFAULT,
        "upvoted": SortType.UPVOTED,
        "newest": SortType.NEWEST
    }

    time_map = {
        "all": TimeInterval.ALL,
        "day": TimeInterval.ONE_DAY,
        "week": TimeInterval.ONE_WEEK,
        "month": TimeInterval.ONE_MONTH,
        "3months": TimeInterval.THREE_MONTHS,
        "6months": TimeInterval.HALF_YEAR,
        "year": TimeInterval.ONE_YEAR
    }

    # 执行搜索
    core = ZhihuSearchCore()
    results = core.search(
        keyword=args.keyword,
        limit=args.num,
        vertical=vertical_map[args.vertical],
        sort=sort_map[args.sort],
        time_interval=time_map[args.time],
        save_response=args.save,
        output_dir=args.output
    )

    # 显示结果
    if results:
        print(f"\n找到 {len(results)} 条结果:\n")
        for i, item in enumerate(results, 1):
            print(f"[{i}] {item.get('type')}: {item.get('title', '')[:60]}")
            if item.get('author'):
                print(f"    作者: {item['author'].get('name', '')}")
            print(f"    赞同: {item.get('stats', {}).get('voteup_count', 0)}")
            print()


if __name__ == "__main__":
    main()
