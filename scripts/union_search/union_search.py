#!/usr/bin/env python3
"""
Union Search - 统一多平台搜索接口

支持同时搜索多个平台，每个平台返回 1-3 条精选结果。

Version: 1.0.0
Author: Claude
License: MIT
"""

import argparse
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# 版本信息
__version__ = "1.0.0"
__author__ = "Claude"

# 添加父目录到路径以便导入其他模块
sys.path.insert(0, str(Path(__file__).parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# =============================================================================
# 平台搜索器映射
# =============================================================================

PLATFORM_MODULES = {
    # 开发者与社区
    "github": {
        "module": "github.github_search",
        "function": "search_github",
        "description": "GitHub 仓库、代码、问题搜索"
    },
    "reddit": {
        "module": "reddit.reddit_search",
        "function": "search_reddit",
        "description": "Reddit 帖子、子版块搜索"
    },

    # 社交媒体
    "xiaohongshu": {
        "module": "xiaohongshu.tikhub_xhs_search",
        "function": "search_xiaohongshu",
        "description": "小红书笔记搜索"
    },
    "douyin": {
        "module": "douyin.tikhub_douyin_search",
        "function": "search_douyin",
        "description": "抖音视频搜索"
    },
    "bilibili": {
        "module": "bilibili.video_search",
        "function": "search_bilibili",
        "description": "Bilibili 视频搜索"
    },
    "youtube": {
        "module": "youtube.youtube_search",
        "function": "search_youtube",
        "description": "YouTube 视频搜索"
    },
    "twitter": {
        "module": "twitter.tikhub_twitter_search",
        "function": "search_twitter",
        "description": "Twitter/X 帖子搜索"
    },
    "weibo": {
        "module": "weibo.weibo_search",
        "function": "search_weibo",
        "description": "微博搜索"
    },
    "zhihu": {
        "module": "zhihu.zhihu_search",
        "function": "search_zhihu",
        "description": "知乎问答搜索"
    },
    "xiaoyuzhoufm": {
        "module": "xiaoyuzhoufm.xiaoyuzhou_search",
        "function": "search_xiaoyuzhoufm",
        "description": "小宇宙FM播客搜索"
    },

    # 搜索引擎
    "google": {
        "module": "google_search.google_search",
        "function": "search_google",
        "description": "Google 搜索"
    },
    "tavily": {
        "module": "tavily_search.tavily_search",
        "function": "search_tavily",
        "description": "Tavily AI 搜索"
    },
    "duckduckgo": {
        "module": "duckduckgo.duckduckgo_search",
        "function": "search_duckduckgo",
        "description": "DuckDuckGo 搜索"
    },
    "brave": {
        "module": "brave.brave_search",
        "function": "search_brave",
        "description": "Brave 搜索"
    },
    "yahoo": {
        "module": "yahoo.yahoo_search",
        "function": "search_yahoo",
        "description": "Yahoo 搜索"
    },
    "bing": {
        "module": "bing.bing_search",
        "function": "search_bing",
        "description": "Bing 搜索"
    },
    "wikipedia": {
        "module": "wikipedia.wikipedia_search",
        "function": "search_wikipedia",
        "description": "Wikipedia 搜索"
    },
    "metaso": {
        "module": "metaso.metaso_search",
        "function": "search_metaso",
        "description": "秘塔搜索 AI 搜索"
    },
    "volcengine": {
        "module": "volcengine.volcengine_search",
        "function": "search_volcengine",
        "description": "火山引擎融合信息搜索"
    },

    # RSS 订阅
    "rss": {
        "module": "rss_search.rss_search",
        "function": "search_rss",
        "description": "RSS Feed 搜索"
    },
}

# 平台分组
PLATFORM_GROUPS = {
    "dev": ["github", "reddit"],
    "social": ["xiaohongshu", "douyin", "bilibili", "youtube", "twitter", "weibo", "zhihu", "xiaoyuzhoufm"],
    "search": ["google", "tavily", "duckduckgo", "brave", "yahoo", "bing", "wikipedia", "metaso", "volcengine"],
    "rss": ["rss"],
    "all": list(PLATFORM_MODULES.keys())
}


# =============================================================================
# 环境变量加载
# =============================================================================

def load_env_file(env_path: str = ".env"):
    """加载 .env 文件"""
    env_file = Path(env_path)
    if not env_file.exists():
        # 尝试从项目根目录加载
        root_env = Path(__file__).parent.parent.parent / ".env"
        if root_env.exists():
            env_file = root_env
        else:
            logger.debug(f"未找到 .env 文件: {env_path}")
            return

    logger.info(f"加载环境变量文件: {env_file}")
    loaded_count = 0

    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value
                loaded_count += 1

    logger.info(f"成功加载 {loaded_count} 个环境变量")


# =============================================================================
# 平台搜索包装器
# =============================================================================

def search_platform(
    platform: str,
    keyword: str,
    limit: int = 3,
    **kwargs
) -> Tuple[str, Dict[str, Any]]:
    """
    搜索单个平台

    Args:
        platform: 平台名称
        keyword: 搜索关键词
        limit: 返回结果数量
        **kwargs: 平台特定参数

    Returns:
        (platform_name, result_dict)
    """
    start_time = datetime.now()
    result = {
        "platform": platform,
        "keyword": keyword,
        "success": False,
        "error": None,
        "items": [],
        "total": 0,
        "timestamp": start_time.isoformat()
    }

    try:
        logger.info(f"开始搜索平台: {platform}, 关键词: {keyword}")

        # 根据平台调用对应的搜索脚本
        if platform == "github":
            result["items"] = _search_github(keyword, limit, **kwargs)
        elif platform == "reddit":
            result["items"] = _search_reddit(keyword, limit, **kwargs)
        elif platform == "xiaohongshu":
            result["items"] = _search_xiaohongshu(keyword, limit, **kwargs)
        elif platform == "douyin":
            result["items"] = _search_douyin(keyword, limit, **kwargs)
        elif platform == "bilibili":
            result["items"] = _search_bilibili(keyword, limit, **kwargs)
        elif platform == "youtube":
            result["items"] = _search_youtube(keyword, limit, **kwargs)
        elif platform == "twitter":
            result["items"] = _search_twitter(keyword, limit, **kwargs)
        elif platform == "weibo":
            result["items"] = _search_weibo(keyword, limit, **kwargs)
        elif platform == "zhihu":
            result["items"] = _search_zhihu(keyword, limit, **kwargs)
        elif platform == "xiaoyuzhoufm":
            result["items"] = _search_xiaoyuzhoufm(keyword, limit, **kwargs)
        elif platform == "google":
            result["items"] = _search_google(keyword, limit, **kwargs)
        elif platform == "tavily":
            result["items"] = _search_tavily(keyword, limit, **kwargs)
        elif platform == "duckduckgo":
            result["items"] = _search_duckduckgo(keyword, limit, **kwargs)
        elif platform == "brave":
            result["items"] = _search_brave(keyword, limit, **kwargs)
        elif platform == "yahoo":
            result["items"] = _search_yahoo(keyword, limit, **kwargs)
        elif platform == "bing":
            result["items"] = _search_bing(keyword, limit, **kwargs)
        elif platform == "wikipedia":
            result["items"] = _search_wikipedia(keyword, limit, **kwargs)
        elif platform == "metaso":
            result["items"] = _search_metaso(keyword, limit, **kwargs)
        elif platform == "volcengine":
            result["items"] = _search_volcengine(keyword, limit, **kwargs)
        elif platform == "rss":
            result["items"] = _search_rss(keyword, limit, **kwargs)
        else:
            result["error"] = f"Unknown platform: {platform}"
            logger.error(result["error"])
            return platform, result

        result["total"] = len(result["items"])
        result["success"] = True

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"平台 {platform} 搜索完成: {result['total']} 条结果, 耗时 {elapsed:.2f}s")

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"平台 {platform} 搜索失败: {e}")

    return platform, result


# =============================================================================
# 平台特定搜索实现（调用各平台脚本）
# =============================================================================

def _search_github(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """GitHub 搜索"""
    import subprocess
    script_path = Path(__file__).parent.parent / "github" / "github_search.py"
    cmd = [sys.executable, str(script_path), "repo", keyword, "--format", "json", "--limit", str(limit)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise Exception(f"GitHub search failed: {result.stderr}")
    data = json.loads(result.stdout)
    return data.get("items", [])[:limit]


def _search_reddit(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """Reddit 搜索"""
    import subprocess
    script_path = Path(__file__).parent.parent / "reddit" / "cli.py"
    # Reddit CLI 使用子命令模式: search, subreddit-search, post, user, subreddit-posts
    cmd = [sys.executable, str(script_path), "search", keyword, "--limit", str(limit), "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise Exception(f"Reddit search failed: {result.stderr}")
    # Reddit CLI 直接返回列表，不需要 items 包装
    data = json.loads(result.stdout)
    return data[:limit] if isinstance(data, list) else []


def _search_xiaohongshu(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """小红书搜索"""
    import subprocess
    script_path = Path(__file__).parent.parent / "xiaohongshu" / "tikhub_xhs_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--limit", str(limit), "--pretty"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise Exception(f"Xiaohongshu search failed: {result.stderr}")
    data = json.loads(result.stdout)
    items = data.get("data", {}).get("items", [])
    return items[:limit]


def _search_douyin(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """抖音搜索"""
    import subprocess
    script_path = Path(__file__).parent.parent / "douyin" / "tikhub_douyin_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--limit", str(limit), "--pretty"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        logger.error(f"Douyin search failed: {result.stderr}")
        return []
    data = json.loads(result.stdout)
    return data.get("items", [])[:limit]


def _search_bilibili(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """Bilibili 搜索"""
    import asyncio
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "bilibili"))
        from video_search import VideoSearcher

        searcher = VideoSearcher()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        videos = loop.run_until_complete(searcher.search(keyword, page_size=limit))
        loop.close()

        items = []
        for v in videos[:limit]:
            items.append({
                "title": v.get("title", ""),
                "url": f"https://www.bilibili.com/video/{v.get('bvid', '')}",
                "bvid": v.get("bvid", ""),
                "author": v.get("author", ""),
                "play_count": v.get("play", 0),
                "duration": v.get("duration", ""),
                "description": v.get("description", "")
            })
        return items
    except Exception as e:
        logger.error(f"Bilibili 搜索失败: {e}")
        return []


def _search_youtube(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """YouTube 搜索"""
    import subprocess
    script_path = Path(__file__).parent.parent / "youtube" / "youtube_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--limit", str(limit), "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        logger.error(f"YouTube search failed: {result.stderr}")
        return []
    try:
        data = json.loads(result.stdout)
        return data[:limit] if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _search_twitter(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """Twitter/X 搜索"""
    import subprocess
    script_path = Path(__file__).parent.parent / "twitter" / "tikhub_twitter_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--pretty"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        logger.error(f"Twitter search failed: {result.stderr}")
        return []
    try:
        data = json.loads(result.stdout)
        # TikHub 返回的数据结构较复杂，简化处理
        items = []
        # 尝试从不同结构中提取数据
        entries = data.get("data", {}).get("data", {}).get("search_by_raw_query", {}).get("search_timeline", {}).get("timeline", {}).get("instructions", [])
        for entry in entries[:limit]:
            if isinstance(entry, dict):
                items.append({
                    "title": entry.get("text", "")[:100] if entry.get("text") else "",
                    "url": f"https://twitter.com/i/web/status/{entry.get('id', '')}",
                    "author": entry.get("author", {}).get("name", ""),
                    "description": entry.get("text", "")
                })
        return items[:limit]
    except Exception as e:
        logger.error(f"Twitter 数据解析失败: {e}")
        return []


def _search_weibo(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """微博搜索 - 需要 cookie 和 user-id"""
    # 微博搜索需要特定的用户ID和cookie配置
    # 返回提示信息而不是实际搜索
    logger.warning("微博搜索需要配置 WEIBO_COOKIE 和 WEIBO_USER_ID")
    return []


def _search_zhihu(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """知乎搜索"""
    import subprocess
    import asyncio
    script_path = Path(__file__).parent.parent / "zhihu" / "zhihu_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--limit", str(limit), "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        logger.error(f"Zhihu search failed: {result.stderr}")
        return []
    try:
        data = json.loads(result.stdout)
        return data[:limit] if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _search_google(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """Google 搜索"""
    import subprocess
    script_path = Path(__file__).parent.parent / "google_search" / "google_search.py"
    cmd = [sys.executable, str(script_path), keyword, "-n", str(limit), "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        logger.error(f"Google search failed: {result.stderr}")
        return []
    try:
        data = json.loads(result.stdout)
        items = []
        for item in data.get("items", [])[:limit]:
            items.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "description": item.get("snippet", "")
            })
        return items
    except json.JSONDecodeError:
        return []


def _search_tavily(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """Tavily AI 搜索"""
    import subprocess
    script_path = Path(__file__).parent.parent / "tavily_search" / "tavily_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--max-results", str(limit), "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        logger.error(f"Tavily search failed: {result.stderr}")
        return []
    try:
        data = json.loads(result.stdout)
        items = []
        for item in data.get("results", [])[:limit]:
            items.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("content", "")
            })
        return items
    except json.JSONDecodeError:
        return []


def _search_duckduckgo(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """DuckDuckGo 搜索"""
    import subprocess
    script_path = Path(__file__).parent.parent / "duckduckgo" / "duckduckgo_search.py"
    cmd = [sys.executable, str(script_path), keyword, "-m", str(limit), "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        logger.error(f"DuckDuckGo search failed: {result.stderr}")
        return []
    try:
        data = json.loads(result.stdout)
        items = []
        for item in data.get("results", [])[:limit]:
            items.append({
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "description": item.get("body", "")
            })
        return items
    except json.JSONDecodeError:
        return []


def _search_brave(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """Brave 搜索"""
    import subprocess
    script_path = Path(__file__).parent.parent / "brave" / "brave_search.py"
    cmd = [sys.executable, str(script_path), keyword, "-m", str(limit), "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        logger.error(f"Brave search failed: {result.stderr}")
        return []
    try:
        data = json.loads(result.stdout)
        items = []
        for item in data.get("results", [])[:limit]:
            items.append({
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "description": item.get("body", "")
            })
        return items
    except json.JSONDecodeError:
        return []


def _search_yahoo(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """Yahoo 搜索"""
    import subprocess
    script_path = Path(__file__).parent.parent / "yahoo" / "yahoo_search.py"
    cmd = [sys.executable, str(script_path), keyword, "-m", str(limit), "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        logger.error(f"Yahoo search failed: {result.stderr}")
        return []
    try:
        data = json.loads(result.stdout)
        return data.get("items", data.get("results", []))[:limit]
    except json.JSONDecodeError:
        return []


def _search_bing(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """Bing 搜索"""
    import subprocess
    script_path = Path(__file__).parent.parent / "bing" / "bing_search.py"
    cmd = [sys.executable, str(script_path), keyword, "-m", str(limit), "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        logger.error(f"Bing search failed: {result.stderr}")
        return []
    try:
        data = json.loads(result.stdout)
        return data.get("items", data.get("results", []))[:limit]
    except json.JSONDecodeError:
        return []


def _search_wikipedia(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """Wikipedia 搜索"""
    import subprocess
    script_path = Path(__file__).parent.parent / "wikipedia" / "wikipedia_search.py"
    cmd = [sys.executable, str(script_path), keyword, "-m", str(limit), "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        logger.error(f"Wikipedia search failed: {result.stderr}")
        return []
    try:
        data = json.loads(result.stdout)
        return data.get("items", data.get("results", []))[:limit]
    except json.JSONDecodeError:
        return []


def _search_metaso(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """秘塔搜索"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "metaso"))
        from metaso_search import MetasoClient

        client = MetasoClient()
        result = client.search(
            query=keyword,
            size=limit,
            include_summary=True
        )

        items = []
        for wp in result.webpages:
            items.append({
                "title": wp.title,
                "url": wp.link,
                "description": wp.summary or wp.snippet or "",
                "score": wp.score,
                "date": wp.date,
                "position": wp.position
            })

        return items
    except Exception as e:
        logger.error(f"Metaso 搜索失败: {e}")
        return []


def _search_volcengine(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """火山引擎搜索"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "volcengine"))
        from volcengine_search import VolcengineSearchClient, load_api_key

        api_key = load_api_key()
        if not api_key:
            logger.error("Volcengine API Key 未设置")
            return []

        client = VolcengineSearchClient(api_key)

        # 使用 web_search_summary 获取 AI 摘要
        result = client.web_search_summary(
            query=keyword,
            count=min(limit, 10)
        )

        if "error" in result:
            logger.error(f"Volcengine 搜索失败: {result['error']}")
            return []

        items = []
        for item in result.get("Data", {}).get("SearchResults", [])[:limit]:
            items.append({
                "title": item.get("Title", ""),
                "url": item.get("Url", ""),
                "description": item.get("Summary", item.get("Snippet", "")),
                "publish_time": item.get("PublishTime", ""),
                "auth_level": item.get("AuthInfoLevel", 0)
            })

        return items
    except Exception as e:
        logger.error(f"Volcengine 搜索失败: {e}")
        return []


def _search_xiaoyuzhoufm(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """小宇宙FM播客搜索"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "xiaoyuzhoufm"))
        from xiaoyuzhou_search import search_podcasts

        result = search_podcasts(
            query=keyword,
            size=limit,
            include_summary=False
        )

        items = []
        for podcast in result.get("podcasts", [])[:limit]:
            items.append({
                "title": podcast.get("title", ""),
                "url": podcast.get("link", ""),
                "description": podcast.get("snippet", ""),
                "author": ", ".join(podcast.get("authors", [])),
                "duration": podcast.get("duration", ""),
                "date": podcast.get("date", ""),
                "score": podcast.get("score", "")
            })

        return items
    except Exception as e:
        logger.error(f"小宇宙FM 搜索失败: {e}")
        return []


def _search_rss(keyword: str, limit: int, **kwargs) -> List[Dict]:
    """RSS Feed 搜索"""
    import subprocess
    script_path = Path(__file__).parent.parent / "rss_search" / "rss_search.py"
    cmd = [sys.executable, str(script_path), keyword, "-l", str(limit), "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        logger.error(f"RSS search failed: {result.stderr}")
        return []
    try:
        data = json.loads(result.stdout)
        items = []
        for item in data[:limit] if isinstance(data, list) else []:
            items.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "description": item.get("summary", ""),
                "author": item.get("author", ""),
                "published": item.get("published", ""),
                "feed_title": item.get("feed_title", "")
            })
        return items
    except json.JSONDecodeError:
        return []


# =============================================================================
# 并发搜索
# =============================================================================

def union_search(
    keyword: str,
    platforms: List[str],
    limit: int = 3,
    max_workers: int = 5,
    timeout: int = 60,
    **kwargs
) -> Dict[str, Any]:
    """
    并发搜索多个平台

    Args:
        keyword: 搜索关键词
        platforms: 平台列表
        limit: 每个平台返回结果数量
        max_workers: 最大并发数
        timeout: 超时时间（秒）
        **kwargs: 平台特定参数

    Returns:
        搜索结果字典
    """
    results = {
        "keyword": keyword,
        "platforms": platforms,
        "limit_per_platform": limit,
        "timestamp": datetime.now().isoformat(),
        "results": {},
        "summary": {
            "total_platforms": len(platforms),
            "successful": 0,
            "failed": 0,
            "total_items": 0
        }
    }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(search_platform, platform, keyword, limit, **kwargs): platform
            for platform in platforms
        }

        completed = 0
        for future in as_completed(futures, timeout=timeout):
            platform = futures[future]
            completed += 1

            try:
                platform_name, result = future.result()
                results["results"][platform_name] = result

                if result["success"]:
                    results["summary"]["successful"] += 1
                    results["summary"]["total_items"] += result["total"]
                    logger.info(f"[{completed}/{len(platforms)}] {platform_name}: 成功 ({result['total']} 条)")
                else:
                    results["summary"]["failed"] += 1
                    logger.warning(f"[{completed}/{len(platforms)}] {platform_name}: 失败 - {result['error']}")

            except Exception as e:
                results["results"][platform] = {
                    "platform": platform,
                    "success": False,
                    "error": str(e),
                    "items": [],
                    "total": 0
                }
                results["summary"]["failed"] += 1
                logger.error(f"[{completed}/{len(platforms)}] {platform}: 异常 - {e}")

    return results


# =============================================================================
# 输出格式化
# =============================================================================

def format_markdown(results: Dict[str, Any]) -> str:
    """格式化为 Markdown"""
    lines = []
    lines.append(f"# 联合搜索结果: {results['keyword']}")
    lines.append(f"\n**搜索时间**: {results['timestamp']}")
    lines.append(f"**平台数量**: {results['summary']['total_platforms']}")
    lines.append(f"**成功**: {results['summary']['successful']} | **失败**: {results['summary']['failed']}")
    lines.append(f"**总结果数**: {results['summary']['total_items']}")
    lines.append("\n---\n")

    for platform, result in results["results"].items():
        lines.append(f"## {platform.upper()}")

        if not result["success"]:
            lines.append(f"\n❌ **错误**: {result['error']}\n")
            continue

        if not result["items"]:
            lines.append("\n⚠️ 无结果\n")
            continue

        lines.append(f"\n✅ 找到 {result['total']} 条结果\n")

        for i, item in enumerate(result["items"], 1):
            lines.append(f"### {i}. {item.get('title', item.get('name', 'N/A'))}")

            # 根据平台显示不同字段
            if "url" in item:
                lines.append(f"- **链接**: {item['url']}")
            if "description" in item:
                desc = item['description'][:200] if item['description'] else ""
                lines.append(f"- **描述**: {desc}...")
            if "author" in item:
                lines.append(f"- **作者**: {item['author']}")
            if "score" in item:
                lines.append(f"- **评分**: {item['score']}")

            lines.append("")

        lines.append("---\n")

    return "\n".join(lines)


def format_json(results: Dict[str, Any], pretty: bool = False) -> str:
    """格式化为 JSON"""
    if pretty:
        return json.dumps(results, ensure_ascii=False, indent=2)
    return json.dumps(results, ensure_ascii=False)


# =============================================================================
# 命令行接口
# =============================================================================

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Union Search - 统一多平台搜索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 搜索所有平台
  python union_search.py "machine learning"

  # 搜索指定平台
  python union_search.py "Python" --platforms github reddit

  # 搜索平台组
  python union_search.py "AI" --group dev

  # 自定义每个平台返回数量
  python union_search.py "深度学习" --limit 5

  # JSON 输出
  python union_search.py "React" --json --pretty

  # 保存结果
  python union_search.py "Vue" -o results.json
        """
    )

    parser.add_argument("keyword", nargs="?", help="搜索关键词")
    parser.add_argument(
        "--platforms", "-p",
        nargs="+",
        help="指定平台列表（空格分隔）"
    )
    parser.add_argument(
        "--group", "-g",
        choices=list(PLATFORM_GROUPS.keys()),
        help="使用预定义平台组: dev, social, search, books, all"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=3,
        help="每个平台返回结果数量（默认: 3）"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=5,
        help="最大并发数（默认: 5）"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="超时时间（秒，默认: 60）"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON 格式输出"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="格式化 JSON 输出"
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Markdown 格式输出（默认）"
    )
    parser.add_argument(
        "-o", "--output",
        help="保存输出到文件"
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="环境变量文件路径"
    )
    parser.add_argument(
        "--list-platforms",
        action="store_true",
        help="列出所有可用平台"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细日志"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Union Search v{__version__}",
        help="显示版本信息"
    )

    return parser.parse_args()


def list_platforms():
    """列出所有可用平台"""
    print("# 可用平台\n")

    print("## 开发者与社区")
    for name in PLATFORM_GROUPS["dev"]:
        print(f"- {name}: {PLATFORM_MODULES[name]['description']}")

    print("\n## 社交媒体")
    for name in PLATFORM_GROUPS["social"]:
        print(f"- {name}: {PLATFORM_MODULES[name]['description']}")

    print("\n## 搜索引擎")
    for name in PLATFORM_GROUPS["search"]:
        print(f"- {name}: {PLATFORM_MODULES[name]['description']}")

    print("\n## 电子书")
    for name in PLATFORM_GROUPS["books"]:
        print(f"- {name}: {PLATFORM_MODULES[name]['description']}")

    print("\n## RSS订阅")
    for name in PLATFORM_GROUPS["rss"]:
        print(f"- {name}: {PLATFORM_MODULES[name]['description']}")

    print("\n## 平台组")
    for group, platforms in PLATFORM_GROUPS.items():
        print(f"- {group}: {', '.join(platforms)}")


def main():
    """主函数"""
    args = parse_args()

    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.INFO)
        logger.info("启用详细日志模式")

    # 列出平台
    if args.list_platforms:
        list_platforms()
        return 0

    # 检查 keyword 是否提供
    if not args.keyword:
        print("错误: 需要提供搜索关键词", file=sys.stderr)
        print("使用 --help 查看帮助", file=sys.stderr)
        return 1

    # 加载环境变量
    load_env_file(args.env_file)

    # 确定要搜索的平台
    if args.platforms:
        platforms = args.platforms
    elif args.group:
        platforms = PLATFORM_GROUPS[args.group]
    else:
        # 默认搜索所有平台
        platforms = PLATFORM_GROUPS["all"]

    # 验证平台
    invalid_platforms = [p for p in platforms if p not in PLATFORM_MODULES]
    if invalid_platforms:
        print(f"错误: 未知平台: {', '.join(invalid_platforms)}", file=sys.stderr)
        print(f"使用 --list-platforms 查看可用平台", file=sys.stderr)
        return 1

    # 执行搜索
    print(f"正在搜索 {len(platforms)} 个平台: {', '.join(platforms)}", file=sys.stderr)
    logger.info(f"搜索参数: keyword={args.keyword}, limit={args.limit}, max_workers={args.max_workers}")

    start_time = datetime.now()
    results = union_search(
        keyword=args.keyword,
        platforms=platforms,
        limit=args.limit,
        max_workers=args.max_workers,
        timeout=args.timeout
    )
    elapsed = (datetime.now() - start_time).total_seconds()

    logger.info(f"搜索完成: 总耗时 {elapsed:.2f}s, 成功 {results['summary']['successful']}/{len(platforms)}")

    # 格式化输出
    if args.json or (args.output and args.output.endswith(".json")):
        output = format_json(results, pretty=args.pretty)
    else:
        output = format_markdown(results)

    # 输出结果
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\n结果已保存到: {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
