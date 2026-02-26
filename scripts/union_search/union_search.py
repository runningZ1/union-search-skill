#!/usr/bin/env python3
"""
Union Search - 统一多平台搜索接口

支持同时搜索多个平台，每个平台返回 1-3 条精选结果。

Version: 1.0.0
Author: Claude
License: MIT
"""

import argparse
import io
import contextlib
import json
import logging
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


def _extract_json_from_text(text: str) -> Any:
    """从包含噪声文本的 stdout 中提取 JSON."""
    if not text:
        raise ValueError("Empty output")

    # 优先尝试整段解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text):
        if ch not in "[{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[idx:])
            return obj
        except json.JSONDecodeError:
            continue

    raise ValueError("No valid JSON found in output")


def _run_platform_json_command(cmd: List[str], timeout: int, platform: str) -> Any:
    """运行平台脚本并安全提取 JSON，容忍 stdout 日志污染."""
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        detail = stderr or stdout or f"exit code {result.returncode}"
        raise Exception(f"{platform} search failed: {detail}")

    try:
        return _extract_json_from_text(result.stdout)
    except ValueError as e:
        stderr = (result.stderr or "").strip()
        detail = f"{e}; stderr={stderr}" if stderr else str(e)
        raise Exception(f"{platform} JSON parse failed: {detail}")


# =============================================================================
# 平台搜索器映射
# =============================================================================

PLATFORM_MODULES = {
    # 开发者与社区
    "github": {
        "module": "github.github_search",
        "function": "search_github",
        "description": "GitHub 仓库、代码、问题搜索",
        "default_limit": None
    },
    "reddit": {
        "module": "reddit.reddit_search",
        "function": "search_reddit",
        "description": "Reddit 帖子、子版块搜索",
        "default_limit": None
    },

    # 社交媒体
    "xiaohongshu": {
        "module": "xiaohongshu.tikhub_xhs_search",
        "function": "search_xiaohongshu",
        "description": "小红书笔记搜索",
        "default_limit": None
    },
    "douyin": {
        "module": "douyin.tikhub_douyin_search",
        "function": "search_douyin",
        "description": "抖音视频搜索",
        "default_limit": None
    },
    "bilibili": {
        "module": "bilibili.video_search",
        "function": "search_bilibili",
        "description": "Bilibili 视频搜索",
        "default_limit": None
    },
    "youtube": {
        "module": "youtube.youtube_search",
        "function": "search_youtube",
        "description": "YouTube 视频搜索",
        "default_limit": None
    },
    "twitter": {
        "module": "twitter.tikhub_twitter_search",
        "function": "search_twitter",
        "description": "Twitter/X 帖子搜索",
        "default_limit": None
    },
    "weibo": {
        "module": "weibo.weibo_search",
        "function": "search_weibo",
        "description": "微博搜索 (需要配置)",
        "default_limit": None
    },
    "zhihu": {
        "module": "zhihu.zhihu_search",
        "function": "search_zhihu",
        "description": "知乎问答搜索",
        "default_limit": None
    },
    "xiaoyuzhoufm": {
        "module": "xiaoyuzhoufm.xiaoyuzhou_search",
        "function": "search_xiaoyuzhoufm",
        "description": "小宇宙FM播客搜索",
        "default_limit": None
    },

    # 搜索引擎
    "google": {
        "module": "google_search.google_search",
        "function": "search_google",
        "description": "Google 搜索",
        "default_limit": None
    },
    "tavily": {
        "module": "tavily_search.tavily_search",
        "function": "search_tavily",
        "description": "Tavily AI 搜索",
        "default_limit": None
    },
    "jina": {
        "module": "jina.jina_search",
        "function": "search_jina",
        "description": "Jina AI 搜索",
        "default_limit": None
    },
    "duckduckgo": {
        "module": "duckduckgo.duckduckgo_search",
        "function": "search_duckduckgo",
        "description": "DuckDuckGo 搜索",
        "default_limit": None
    },
    "brave": {
        "module": "brave.brave_search",
        "function": "search_brave",
        "description": "Brave 搜索",
        "default_limit": None
    },
    "yahoo": {
        "module": "yahoo.yahoo_search",
        "function": "search_yahoo",
        "description": "Yahoo 搜索",
        "default_limit": None
    },
    "yandex": {
        "module": "yandex.yandex_search",
        "function": "search_yandex",
        "description": "Yandex 搜索 (SerpAPI)",
        "default_limit": None
    },
    "bing": {
        "module": "bing.bing_serpapi_search",
        "function": "search_bing",
        "description": "Bing 搜索 (SerpAPI)",
        "default_limit": None
    },
    "wikipedia": {
        "module": "wikipedia.wikipedia_search",
        "function": "search_wikipedia",
        "description": "Wikipedia 搜索",
        "default_limit": None
    },
    "metaso": {
        "module": "metaso.metaso_search",
        "function": "search_metaso",
        "description": "秘塔搜索 AI 搜索",
        "default_limit": None
    },
    "volcengine": {
        "module": "volcengine.volcengine_search",
        "function": "search_volcengine",
        "description": "火山引擎融合信息搜索",
        "default_limit": None
    },
    "baidu": {
        "module": "baidu.baidu_search",
        "function": "search_baidu",
        "description": "百度千帆搜索",
        "default_limit": None
    },
    # RSS 订阅

    "rss": {
        "module": "rss_search.rss_search",
        "function": "search_rss",
        "description": "RSS Feed 搜索",
        "default_limit": None
    },
}

# 平台分组
PLATFORM_GROUPS = {
    "dev": ["github", "reddit"],
    "social": ["douyin", "bilibili", "youtube", "twitter", "weibo", "zhihu", "xiaoyuzhoufm"],
    "search": ["google", "tavily", "jina", "duckduckgo", "brave", "yahoo", "yandex", "bing", "wikipedia", "metaso", "volcengine", "baidu"],
    "rss": ["rss"],
    "all": [p for p in PLATFORM_MODULES.keys() if p != "xiaohongshu"]
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
    limit: Optional[int] = None,
    **kwargs
) -> Tuple[str, Dict[str, Any]]:
    """
    搜索单个平台

    Args:
        platform: 平台名称
        keyword: 搜索关键词
        limit: 返回结果数量 (如果为 None, 使用平台默认值)
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
        "timestamp": start_time.isoformat(),
        "timing_ms": 0
    }

    try:
        logger.info(f"开始搜索平台: {platform}, 关键词: {keyword}")

        # 根据平台调用对应的搜索脚本
        if platform == "github":
            result["items"] = _search_github(keyword, limit, **kwargs)
        elif platform == "reddit":
            result["items"] = _search_reddit(keyword, limit, **kwargs)
        elif platform == "xiaohongshu":
            result["error"] = "xiaohongshu search is temporarily disabled"
            logger.warning(result["error"])
            return platform, result
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
        elif platform == "jina":
            result["items"] = _search_jina(keyword, limit, **kwargs)
        elif platform == "duckduckgo":
            result["items"] = _search_duckduckgo(keyword, limit, **kwargs)
        elif platform == "brave":
            result["items"] = _search_brave(keyword, limit, **kwargs)
        elif platform == "yahoo":
            result["items"] = _search_yahoo(keyword, limit, **kwargs)
        elif platform == "yandex":
            result["items"] = _search_yandex(keyword, limit, **kwargs)
        elif platform == "bing":
            result["items"] = _search_bing(keyword, limit, **kwargs)
        elif platform == "wikipedia":
            result["items"] = _search_wikipedia(keyword, limit, **kwargs)
        elif platform == "metaso":
            result["items"] = _search_metaso(keyword, limit, **kwargs)
        elif platform == "volcengine":
            result["items"] = _search_volcengine(keyword, limit, **kwargs)
        elif platform == "baidu":
            result["items"] = _search_baidu(keyword, limit, **kwargs)
        elif platform == "rss":

            result["items"] = _search_rss(keyword, limit, **kwargs)
        else:
            result["error"] = f"Unknown platform: {platform}"
            logger.error(result["error"])
            return platform, result

        result["total"] = len(result["items"])
        result["success"] = True

        elapsed = (datetime.now() - start_time).total_seconds()
        result["timing_ms"] = int(elapsed * 1000)
        logger.info(f"平台 {platform} 搜索完成: {result['total']} 条结果, 耗时 {elapsed:.2f}s")

    except Exception as e:
        result["error"] = str(e)
        elapsed = (datetime.now() - start_time).total_seconds()
        result["timing_ms"] = int(elapsed * 1000)
        logger.error(f"平台 {platform} 搜索失败: {e}")

    return platform, result


# =============================================================================
# 平台特定搜索实现（调用各平台脚本）
# =============================================================================

def _search_github(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """GitHub 搜索"""
    script_path = Path(__file__).parent.parent / "github" / "github_search.py"
    cmd = [sys.executable, str(script_path), "repo", keyword, "--format", "json"]
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="github")
    items = data.get("items", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_reddit(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Reddit 搜索"""
    script_path = Path(__file__).parent.parent / "reddit" / "cli.py"
    # Reddit CLI 使用子命令模式: search, subreddit-search, post, user, subreddit-posts
    cmd = [sys.executable, str(script_path), "search", keyword, "--format", "json"]
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip() or f"exit code {result.returncode}"
        raise Exception(f"reddit search failed: {detail}")

    # yars 在请求失败时会输出错误文本 + []，这里显式判定为失败而不是“空结果成功”
    failure_markers = ["Failed to fetch search results", "错误:"]
    merged = f"{result.stdout}\n{result.stderr}"
    if any(marker in merged for marker in failure_markers):
        raise Exception(merged.strip())

    data = _extract_json_from_text(result.stdout)
    if not isinstance(data, list):
        return []
    return data[:limit] if limit is not None else data


def _search_xiaohongshu(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """小红书搜索"""
    script_path = Path(__file__).parent.parent / "xiaohongshu" / "tikhub_xhs_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--pretty"]
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="xiaohongshu")
    # 数据直接在根级别的 items 字段
    items = data.get("items", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_douyin(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """抖音搜索"""
    script_path = Path(__file__).parent.parent / "douyin" / "tikhub_douyin_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--pretty"]
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    data = _run_platform_json_command(cmd, timeout=60, platform="douyin")
    items = data.get("items", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_bilibili(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Bilibili 搜索"""
    import asyncio
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "bilibili"))
        from video_search import VideoSearcher

        page_size = limit if limit is not None else 10
        searcher = VideoSearcher()
        # 某些 SDK 会直接 print 到 stdout，这里拦截避免污染 union_search 输出
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            videos = loop.run_until_complete(searcher.search(keyword, page_size=page_size))
            loop.close()
        return videos[:limit] if isinstance(videos, list) and limit is not None else (videos if isinstance(videos, list) else [])
    except Exception as e:
        raise Exception(f"Bilibili 搜索失败: {e}")


def _search_youtube(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """YouTube 搜索"""
    script_path = Path(__file__).parent.parent / "youtube" / "youtube_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    data = _run_platform_json_command(cmd, timeout=60, platform="youtube")
    if not isinstance(data, list):
        return []
    return data[:limit] if limit is not None else data


def _search_twitter(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Twitter/X 搜索"""
    script_path = Path(__file__).parent.parent / "twitter" / "tikhub_twitter_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--pretty"]
    data = _run_platform_json_command(cmd, timeout=60, platform="twitter")
    # 兼容当前脚本返回结构: data.timeline
    timeline = data.get("data", {}).get("timeline", [])
    if isinstance(timeline, list):
        return timeline[:limit] if limit is not None else timeline
    return []


def _search_weibo(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """微博搜索 - 需要 cookie 和 user-id"""
    # 微博搜索需要特定的用户ID和cookie配置
    raise Exception("微博搜索需要配置 WEIBO_COOKIE 和 WEIBO_USER_ID")


def _search_zhihu(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """知乎搜索"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "zhihu"))
        from zhihu_core import ZhihuSearchCore, logger as zhihu_logger

        # zhihu_core 使用 loguru 全局 logger，临时移除 sinks 避免污染输出
        try:
            zhihu_logger.remove()
        except Exception:
            pass
        zhihu_logger.add(lambda _: None)

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            core = ZhihuSearchCore()
            items = core.search(keyword=keyword, limit=limit if limit is not None else 20)
        return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])
    except Exception as e:
        raise Exception(f"Zhihu search failed: {e}")


def _search_google(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Google 搜索"""
    script_path = Path(__file__).parent.parent / "google_search" / "google_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-n", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="google")
    items = data.get("items", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_tavily(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Tavily AI 搜索"""
    script_path = Path(__file__).parent.parent / "tavily_search" / "tavily_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["--max-results", str(limit)])
    data = _run_platform_json_command(cmd, timeout=60, platform="tavily")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_jina(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Jina AI 搜索"""
    script_path = Path(__file__).parent.parent / "jina" / "jina_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    data = _run_platform_json_command(cmd, timeout=60, platform="jina")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_duckduckgo(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """DuckDuckGo 搜索"""
    script_path = Path(__file__).parent.parent / "duckduckgo" / "duckduckgo_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="duckduckgo")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_brave(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Brave 搜索"""
    script_path = Path(__file__).parent.parent / "brave" / "brave_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="brave")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_yahoo(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Yahoo 搜索"""
    script_path = Path(__file__).parent.parent / "yahoo" / "yahoo_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="yahoo")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_yandex(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Yandex 搜索"""
    script_path = Path(__file__).parent.parent / "yandex" / "yandex_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="yandex")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_bing(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Bing 搜索"""
    script_path = Path(__file__).parent.parent / "bing" / "bing_serpapi_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="bing")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_wikipedia(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Wikipedia 搜索"""
    script_path = Path(__file__).parent.parent / "wikipedia" / "wikipedia_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    # 中文关键词优先使用中文 Wikipedia
    if any('\u4e00' <= ch <= '\u9fff' for ch in keyword):
        cmd.extend(["-l", "zh"])
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="wikipedia")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_metaso(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """秘塔搜索"""
    script_path = Path(__file__).parent.parent / "metaso" / "metaso_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--format", "json", "--summary"]
    if limit is not None:
        cmd.extend(["--size", str(limit)])
    data = _run_platform_json_command(cmd, timeout=60, platform="metaso")
    items = data.get("webpages", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_volcengine(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """火山引擎搜索"""
    script_path = Path(__file__).parent.parent / "volcengine" / "volcengine_search.py"
    cmd = [sys.executable, str(script_path), "summary", keyword]
    if limit is not None:
        cmd.extend(["--count", str(limit)])
    data = _run_platform_json_command(cmd, timeout=60, platform="volcengine")
    if isinstance(data, dict) and data.get("error"):
        raise Exception(str(data.get("error")))
    # 兼容不同版本返回结构：
    # - 当前脚本: Result.WebResults
    # - 历史结构: Data.SearchResults
    items: Any = []
    if isinstance(data, dict):
        result_obj = data.get("Result")
        if isinstance(result_obj, dict):
            items = result_obj.get("WebResults", [])
        if not isinstance(items, list):
            items = data.get("Data", {}).get("SearchResults", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_baidu(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """百度千帆搜索"""
    script_path = Path(__file__).parent.parent / "baidu" / "baidu_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-l", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="baidu")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_xiaoyuzhoufm(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:

    """小宇宙FM播客搜索"""
    script_path = Path(__file__).parent.parent / "xiaoyuzhoufm" / "xiaoyuzhou_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["--size", str(limit)])
    data = _run_platform_json_command(cmd, timeout=60, platform="xiaoyuzhoufm")
    items = data.get("podcasts", []) if isinstance(data, dict) else []
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_rss(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """RSS Feed 搜索"""
    script_path = Path(__file__).parent.parent / "rss_search" / "rss_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-l", str(limit)])
    data = _run_platform_json_command(cmd, timeout=60, platform="rss")
    if not isinstance(data, list):
        return []
    return data[:limit] if limit is not None else data


# =============================================================================
# 并发搜索
# =============================================================================

def union_search(
    keyword: str,
    platforms: List[str],
    limit: Optional[int] = None,
    max_workers: int = 5,
    timeout: int = 60,
    **kwargs
) -> Dict[str, Any]:
    """
    并发搜索多个平台

    Args:
        keyword: 搜索关键词
        platforms: 平台列表
        limit: 每个平台返回结果数量 (如果为 None, 使用各平台默认值)
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
                    "total": 0,
                    "timing_ms": 0
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


def write_text_atomic(path: str, content: str):
    """原子写入文本文件，避免部分写入。"""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target.with_suffix(target.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(temp_path, target)


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
        default=None,
        help="每个平台返回结果数量 (默认: 使用各平台自身默认值)"
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
        write_text_atomic(args.output, output)
        print(f"\n结果已保存到: {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
