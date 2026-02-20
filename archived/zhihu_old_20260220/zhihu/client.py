"""
知乎搜索模块 - API 客户端

使用 httpx 处理知乎 API 请求
"""
import asyncio
import json
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode

import httpx
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .signature import ZhihuSignature
from .exception import (
    ZhihuNetworkError,
    ZhihuForbiddenError,
    ZhihuRateLimitError,
    ZhihuNotFoundError,
)


class ZhihuAPIClient:
    """知乎 API 客户端

    处理与知乎 API 的 HTTP 通信
    """

    # API 端点
    BASE_URL = "https://www.zhihu.com"
    SEARCH_API = "/api/v4/search_v3"

    # 请求配置
    DEFAULT_TIMEOUT = 30.0  # 秒
    DEFAULT_DELAY = 1.5     # 请求间隔（秒）

    def __init__(
        self,
        cookies: Optional[List[Dict]] = None,
        timeout: float = DEFAULT_TIMEOUT,
        delay: float = DEFAULT_DELAY,
    ):
        """初始化 API 客户端

        Args:
            cookies: Cookie 列表（从 Playwright 获取）
            timeout: 请求超时时间（秒）
            delay: 请求间隔（秒）
        """
        self.cookies = cookies or []
        self.timeout = timeout
        self.delay = delay

        # 构建请求头
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://www.zhihu.com",
            "Referer": "https://www.zhihu.com/search",
        }

        # 创建 HTTP 客户端
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=timeout,
            follow_redirects=True,
        )

        # 最后请求时间（用于速率控制）
        self._last_request_time: Optional[float] = None

        logger.debug(f"知乎 API 客户端初始化 - cookies={len(self.cookies)}, timeout={timeout}")

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
        logger.debug("知乎 API 客户端已关闭")

    def _build_cookie_header(self) -> str:
        """构建 Cookie 请求头"""
        if not self.cookies:
            return ""

        cookie_pairs = []
        for cookie in self.cookies:
            name = cookie.get("name", "")
            value = cookie.get("value", "")
            if name and value:
                cookie_pairs.append(f"{name}={value}")

        return "; ".join(cookie_pairs)

    async def _wait_for_rate_limit(self):
        """等待以符合请求频率限制"""
        if self._last_request_time is not None:
            elapsed = asyncio.get_event_loop().time() - self._last_request_time
            if elapsed < self.delay:
                await asyncio.sleep(self.delay - elapsed)

        self._last_request_time = asyncio.get_event_loop().time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
    )
    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送 HTTP 请求

        Args:
            method: HTTP 方法（GET/POST）
            path: API 路径
            params: URL 查询参数
            data: 请求体数据
            **kwargs: 额外的请求参数

        Returns:
            API 响应 JSON 数据

        Raises:
            ZhihuNetworkError: 网络请求失败
            ZhihuForbiddenError: 访问被禁止 (403)
            ZhihuRateLimitError: 请求频率限制 (429)
            ZhihuNotFoundError: 内容未找到 (404)
        """
        await self._wait_for_rate_limit()

        # 添加 Cookie
        headers = kwargs.pop("headers", {})
        cookie_header = self._build_cookie_header()
        if cookie_header:
            headers["Cookie"] = cookie_header

        url = f"{self.BASE_URL}{path}"

        try:
            logger.debug(f"API 请求: {method} {path}")
            if params:
                logger.debug(f"  参数: {params}")

            response = await self.client.request(
                method=method,
                url=path,
                params=params,
                json=data,
                headers=headers,
                **kwargs,
            )

            # 处理 HTTP 错误状态
            if response.status_code == 403:
                raise ZhihuForbiddenError("访问被禁止，可能需要更新 Cookie 或检查签名")
            elif response.status_code == 429:
                raise ZhihuRateLimitError("请求过于频繁，请稍后再试")
            elif response.status_code == 404:
                raise ZhihuNotFoundError("请求的资源不存在")
            elif response.status_code >= 400:
                raise ZhihuNetworkError(f"API 请求失败: HTTP {response.status_code}")

            # 解析 JSON 响应
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 状态错误: {e}")
            raise ZhihuNetworkError(f"HTTP 请求失败: {e}") from e
        except httpx.RequestError as e:
            logger.error(f"网络请求错误: {e}")
            raise ZhihuNetworkError(f"网络请求失败: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            raise ZhihuNetworkError(f"响应数据解析失败: {e}") from e

    async def search(
        self,
        keyword: str,
        search_type: str = "content",
        limit: int = 20,
        offset: int = 0,
        sort: str = "default",
        filter_fields: str = "",
    ) -> Dict[str, Any]:
        """执行搜索请求

        Args:
            keyword: 搜索关键词
            search_type: 搜索类型 (content/article/people)
            limit: 每页数量 (最大 20)
            offset: 偏移量
            sort: 排序方式 (default/relevance/time/vote)
            filter_fields: 过滤字段

        Returns:
            API 响应数据
        """
        # 构建查询参数
        params = {
            "q": keyword,
            "vertical": search_type,
            "limit": min(limit, 20),  # 知乎 API 限制最多 20 条
            "offset": offset,
            "sort": sort,
            "filter_fields": filter_fields,
            "lc_idx": 0,
        }

        # 暂时不使用签名，只使用基础头
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        # 添加 Cookie
        cookie_header = self._build_cookie_header()
        if cookie_header:
            headers["Cookie"] = cookie_header

        return await self._request("GET", self.SEARCH_API, params=params, headers=headers)

    async def get_answer_detail(self, answer_id: str) -> Dict[str, Any]:
        """获取回答详情

        Args:
            answer_id: 回答 ID

        Returns:
            回答详情数据
        """
        path = f"/api/v4/answers/{answer_id}"
        return await self._request("GET", path)

    async def get_article_detail(self, article_id: str) -> Dict[str, Any]:
        """获取文章详情

        Args:
            article_id: 文章 ID

        Returns:
            文章详情数据
        """
        path = f"/api/v4/articles/{article_id}"
        return await self._request("GET", path)

    async def get_question_detail(self, question_id: str) -> Dict[str, Any]:
        """获取问题详情

        Args:
            question_id: 问题 ID

        Returns:
            问题详情数据
        """
        path = f"/api/v4/questions/{question_id}"
        return await self._request("GET", path)

    async def get_comments(
        self,
        question_id: str,
        answer_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """获取评论列表

        Args:
            question_id: 问题 ID
            answer_id: 回答 ID
            limit: 每页数量
            offset: 偏移量

        Returns:
            评论列表数据
        """
        path = f"/api/v4/questions/{question_id}/answers/{answer_id}/comments"
        params = {
            "limit": limit,
            "offset": offset,
            "order": "normal",
        }
        return await self._request("GET", path, params=params)
