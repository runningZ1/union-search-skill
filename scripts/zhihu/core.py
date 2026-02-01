"""
知乎搜索模块 - 核心搜索客户端

使用 Playwright + API 混合模式实现知乎搜索功能
"""
import asyncio
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from loguru import logger
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .field import SearchType, SearchSort, SearchTimeRange
from .exception import (
    ZhihuCookieError,
    ZhihuAuthError,
    ZhihuForbiddenError,
    ZhihuNetworkError,
)
from .client import ZhihuAPIClient
from .extractor import ZhihuExtractor
from .signature import ZhihuSignature
from .fetcher import ZhihuContentFetcher
from urllib.parse import quote


# 加载环境变量
def load_env_file(path: str = None) -> None:
    """加载 .env 文件中的配置"""
    if path is None:
        # 默认使用项目根目录的 .env 文件
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"
    else:
        env_file = Path(path)

    if env_file.exists():
        load_dotenv(env_file)
        logger.debug(f"已加载环境变量文件: {env_file}")


class ZhihuSearchClient:
    """知乎搜索客户端

    使用 Playwright 获取 Cookie，然后通过 API 调用实现搜索功能
    """

    # 知乎 API 端点
    BASE_URL = "https://www.zhihu.com"
    SEARCH_API = "/api/v4/search_v3"

    # 默认配置
    DEFAULT_TIMEOUT = 30000  # 30秒
    DEFAULT_DELAY = 1.5      # 请求间隔（秒）
    MAX_RETRIES = 3          # 最大重试次数

    # User-Agent
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        cookie: Optional[str] = None,
        headless: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        user_data_dir: Optional[str] = None,
    ):
        """初始化知乎搜索客户端

        Args:
            cookie: 知乎 Cookie 字符串（可选，优先使用）
            headless: 是否使用无头浏览器模式
            timeout: 请求超时时间（毫秒）
            user_data_dir: 浏览器用户数据目录（用于持久化登录态）
        """
        self.cookie = cookie or os.getenv("ZHIHU_COOKIE")
        self.headless = headless
        self.timeout = timeout
        self.user_data_dir = user_data_dir

        # 浏览器和上下文
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # Cookie 存储
        self.cookies: List[Dict] = []

        # API 客户端（在获取 Cookie 后初始化）
        self.api_client: Optional[ZhihuAPIClient] = None

        logger.info(f"知乎搜索客户端初始化 - headless={headless}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def start(self):
        """启动浏览器并初始化"""
        await self._init_browser()
        await self._init_cookies()

    async def _init_browser(self):
        """初始化 Playwright 浏览器"""
        logger.info("正在启动 Playwright 浏览器...")

        self.playwright = await async_playwright().start()

        # 启动参数
        launch_args = {
            "headless": self.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        }

        # 如果指定了用户数据目录，使用持久化上下文
        if self.user_data_dir:
            logger.debug(f"使用持久化浏览器上下文: {self.user_data_dir}")
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                user_agent=self.USER_AGENT,
                **launch_args,
            )
            self.browser = self.context.browser
        else:
            self.browser = await self.playwright.chromium.launch(**launch_args)
            self.context = await self.browser.new_context(
                user_agent=self.USER_AGENT,
                viewport={"width": 1920, "height": 1080},
            )

        # 添加 stealth 脚本（如果存在）
        stealth_script_path = Path(__file__).parent / "libs" / "stealth.min.js"
        if stealth_script_path.exists():
            with open(stealth_script_path, "r", encoding="utf-8") as f:
                stealth_script = f.read()
            await self.context.add_init_script(stealth_script)
            logger.debug("已加载 stealth.min.js 反检测脚本")
        else:
            logger.warning("未找到 stealth.min.js，反检测能力可能受限")

        # 创建页面
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)

        logger.info("Playwright 浏览器启动成功")

    async def _init_cookies(self):
        """初始化 Cookie"""
        if self.cookie:
            # 从环境变量或参数中获取 Cookie
            logger.info("使用配置的 Cookie")
            await self._set_cookie_from_string(self.cookie)
        else:
            # 通过访问知乎首页获取 Cookie
            logger.info("未配置 Cookie，将通过访问知乎获取")
            await self._fetch_cookies_from_zhihu()

        # 获取 Cookie 后更新到上下文
        self.cookies = await self.context.cookies()

        # 初始化 API 客户端
        self.api_client = ZhihuAPIClient(
            cookies=self.cookies,
            timeout=self.timeout / 1000,  # 转换为秒
            delay=self.DEFAULT_DELAY,
        )
        logger.info("API 客户端已初始化")

    async def _set_cookie_from_string(self, cookie_string: str):
        """从 Cookie 字符串设置 Cookie"""
        try:
            # 解析 Cookie 字符串（格式：name1=value1; name2=value2）
            for part in cookie_string.split(";"):
                part = part.strip()
                if "=" in part:
                    name, value = part.split("=", 1)
                    await self.context.add_cookies([{
                        "name": name.strip(),
                        "value": value.strip(),
                        "domain": ".zhihu.com",
                        "path": "/",
                    }])

            logger.info("Cookie 设置成功")
        except Exception as e:
            raise ZhihuCookieError(f"Cookie 解析失败: {e}") from e

    async def _fetch_cookies_from_zhihu(self):
        """通过访问知乎获取 Cookie"""
        try:
            logger.debug("正在访问知乎首页...")
            await self.page.goto(self.BASE_URL, wait_until="networkidle")
            await asyncio.sleep(1)

            # 获取当前 Cookie
            self.cookies = await self.context.cookies()
            logger.info(f"已获取 {len(self.cookies)} 个 Cookie")

        except Exception as e:
            raise ZhihuNetworkError(f"获取 Cookie 失败: {e}") from e

    async def search(
        self,
        keyword: str,
        search_type: SearchType = SearchType.CONTENT,
        limit: int = 10,
        sort: SearchSort = SearchSort.DEFAULT,
        time_range: Optional[SearchTimeRange] = None,
        full_content: bool = False,
        include_comments: bool = False,
    ) -> List[Dict[str, Any]]:
        """执行搜索

        Args:
            keyword: 搜索关键词
            search_type: 搜索类型
            limit: 返回结果数量
            sort: 排序方式
            time_range: 时间范围过滤（暂未实现）
            full_content: 是否获取完整内容
            include_comments: 是否包含评论

        Returns:
            搜索结果列表
        """
        logger.info(f"搜索: keyword='{keyword}', type={search_type.value}, limit={limit}, sort={sort.value}")

        # 导航到搜索页面（用于更新 Cookie 和获取最新的会话信息）
        await self._navigate_to_search(keyword, search_type)

        # 更新 API 客户端的 Cookie
        self.cookies = await self.context.cookies()
        if self.api_client:
            self.api_client.cookies = self.cookies

        # 调用搜索 API
        try:
            api_response = await self.api_client.search(
                keyword=keyword,
                search_type=search_type.value,
                limit=limit,
                offset=0,
                sort=sort.value,
            )

            # 提取数据
            data = api_response.get("data", [])
            results = ZhihuExtractor.extract_search_results(data, start_rank=1)

            # 获取完整内容（如果需要）
            if full_content or include_comments:
                fetcher = ZhihuContentFetcher(self.api_client)
                results = await fetcher.fetch_batch_full_content(
                    results,
                    include_comments=include_comments,
                )

            logger.info(f"搜索完成，返回 {len(results)} 条结果")
            return results

        except ZhihuForbiddenError as e:
            logger.error(f"搜索失败: {e}")
            raise
        except ZhihuNetworkError as e:
            logger.error(f"网络错误: {e}")
            raise
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    async def _navigate_to_search(self, keyword: str, search_type: SearchType):
        """导航到搜索页面（用于更新 Cookie）"""
        # 对关键词进行 URL 编码
        encoded_keyword = quote(keyword)
        url = f"{self.BASE_URL}/search?type={search_type.value}&q={encoded_keyword}"
        logger.debug(f"导航到搜索页: {url}")

        try:
            await self.page.goto(url, wait_until="networkidle")
            await asyncio.sleep(self.DEFAULT_DELAY)
        except Exception as e:
            logger.warning(f"导航到搜索页失败: {e}")

    async def close(self):
        """关闭浏览器和清理资源"""
        logger.info("正在关闭浏览器...")

        # 关闭 API 客户端
        if self.api_client:
            await self.api_client.close()

        if self.page and not self.page.is_closed():
            await self.page.close()

        if self.context:
            await self.context.close()

        if self.browser and self.browser.is_connected():
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

        logger.info("浏览器已关闭")


# 便捷函数
async def search_zhihu(
    keyword: str,
    search_type: SearchType = SearchType.CONTENT,
    limit: int = 10,
    sort: SearchSort = SearchSort.DEFAULT,
    cookie: Optional[str] = None,
    headless: bool = True,
) -> List[Dict[str, Any]]:
    """便捷的搜索函数

    Args:
        keyword: 搜索关键词
        search_type: 搜索类型
        limit: 返回结果数量
        sort: 排序方式
        cookie: Cookie 字符串
        headless: 是否无头模式

    Returns:
        搜索结果列表
    """
    async with ZhihuSearchClient(cookie=cookie, headless=headless) as client:
        return await client.search(
            keyword=keyword,
            search_type=search_type,
            limit=limit,
            sort=sort,
        )
