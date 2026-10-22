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
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse, urlunparse

from dotenv import load_dotenv

# 版本信息
__version__ = "1.0.0"
__author__ = "Claude"

# 添加 scripts/ 与 scripts/channels/ 到路径以便导入其他模块
CHANNELS_DIR = Path(__file__).resolve().parents[1] / "channels"
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(CHANNELS_DIR))

# 导入搜索日志记录器
from .search_logger import SearchLogger

# URL转Markdown模块（可选导入）
try:
    from ..url_to_markdown import UrlToMarkdown
    URL_TO_MARKDOWN_AVAILABLE = True
except ImportError:
    URL_TO_MARKDOWN_AVAILABLE = False

# 配置日志 - 输出到 stderr，与 JSON 输出分离
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s%(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True,
    stream=sys.stderr  # 日志输出到 stderr，JSON 输出到 stdout
)
logger = logging.getLogger(__name__)


def _normalize_title(value: str) -> str:
    """规范化标题用于去重。"""
    if not value:
        return ""
    text = re.sub(r"\s+", " ", value).strip().casefold()
    return text


def _normalize_link(value: str) -> str:
    """规范化链接用于去重，尽量去除跳转和常见跟踪参数。"""
    if not value:
        return ""
    link = value.strip()
    if not link:
        return ""

    parsed = urlparse(link)

    # 处理 Yahoo 跳转链接，优先取真实目标 RU 参数。
    if parsed.netloc.casefold().endswith("search.yahoo.com"):
        ru_values = parse_qs(parsed.query).get("RU")
        if not ru_values:
            match = re.search(r"/RU=([^/]+)/", parsed.path)
            if match:
                ru_values = [match.group(1)]
        if ru_values:
            link = unquote(ru_values[0])
            parsed = urlparse(link)

    if not parsed.scheme or not parsed.netloc:
        return link.casefold()

    filtered_query_pairs = []
    tracking_keys = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"}
    for pair in parsed.query.split("&"):
        if not pair:
            continue
        key = pair.split("=", 1)[0].casefold()
        if key in tracking_keys or key.startswith("utm_"):
            continue
        filtered_query_pairs.append(pair)

    normalized_path = parsed.path.rstrip("/")
    normalized = urlunparse((
        parsed.scheme.casefold(),
        parsed.netloc.casefold(),
        normalized_path,
        "",
        "&".join(filtered_query_pairs),
        ""
    ))
    return normalized


def _extract_title_and_link(item: Dict[str, Any]) -> Tuple[str, str]:
    """从平台结果中提取标题和链接。"""
    title = str(item.get("title") or item.get("name") or "").strip()
    link = ""
    for key in ("href", "url", "link", "permalink", "source_url"):
        value = item.get(key)
        if value:
            link = str(value).strip()
            break
    return title, link


def _deduplicate_items(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """按标题或链接去重，返回去重后结果及去重条数。"""
    deduped: List[Dict[str, Any]] = []
    seen_titles = set()
    seen_links = set()
    removed = 0

    for item in items:
        title, link = _extract_title_and_link(item)
        title_key = _normalize_title(title)
        link_key = _normalize_link(link)

        duplicated_by_title = bool(title_key) and title_key in seen_titles
        duplicated_by_link = bool(link_key) and link_key in seen_links

        if duplicated_by_title or duplicated_by_link:
            removed += 1
            continue

        if title_key:
            seen_titles.add(title_key)
        if link_key:
            seen_links.add(link_key)
        deduped.append(item)

    return deduped, removed


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


def _run_platform_json_command(cmd: List[str], timeout: int, platform: str, env: Optional[Dict[str, str]] = None) -> Any:
    """运行平台脚本并安全提取 JSON，容忍 stdout 日志污染."""
    # 合并环境变量（子进程继承父进程环境 + 额外传入的变量）
    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=run_env)

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
        "module": "github_search.github_search",
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
    "youtube": {
        "module": "youtube.youtube_search",
        "function": "search_youtube",
        "description": "YouTube 视频搜索",
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

    # === 无需 API Key 搜索引擎 ===
    "baidu_direct": {
        "module": "baidu.baidu_no_api",
        "function": "search_baidu",
        "description": "百度搜索（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "bing_cn_direct": {
        "module": "bing.bing_cn_no_api",
        "function": "search_bing_cn",
        "description": "Bing 中国（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "bing_int_direct": {
        "module": "bing.bing_int_no_api",
        "function": "search_bing_int",
        "description": "Bing 国际（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "so360_direct": {
        "module": "so360.so360_no_api",
        "function": "search_so360",
        "description": "360 搜索（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "sogou_direct": {
        "module": "sogou.sogou_no_api",
        "function": "search_sogou",
        "description": "搜狗搜索（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "toutiao_direct": {
        "module": "toutiao.toutiao_no_api",
        "function": "search_toutiao",
        "description": "头条搜索（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "jisilu_direct": {
        "module": "jisilu.jisilu_no_api",
        "function": "search_jisilu",
        "description": "集思录搜索（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "google_direct": {
        "module": "google_search.google_no_api",
        "function": "search_google",
        "description": "Google 搜索（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "google_hk_direct": {
        "module": "google_search.google_hk_no_api",
        "function": "search_google_hk",
        "description": "Google 香港（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "duckduckgo_html": {
        "module": "duckduckgo.duckduckgo_no_api",
        "function": "search_duckduckgo_html",
        "description": "DuckDuckGo HTML（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "startpage_direct": {
        "module": "startpage.startpage_no_api",
        "function": "search_startpage",
        "description": "Startpage 隐私搜索（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "brave_direct": {
        "module": "brave.brave_no_api",
        "function": "search_brave",
        "description": "Brave 搜索（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "yahoo_direct": {
        "module": "yahoo.yahoo_no_api",
        "function": "search_yahoo",
        "description": "Yahoo 搜索（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "ecosia_direct": {
        "module": "ecosia.ecosia_no_api",
        "function": "search_ecosia",
        "description": "Ecosia 环保搜索（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "qwant_direct": {
        "module": "qwant.qwant_no_api",
        "function": "search_qwant",
        "description": "Qwant 欧洲搜索（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "wolfram_direct": {
        "module": "wolfram.wolfram_no_api",
        "function": "search_wolfram",
        "description": "WolframAlpha 知识计算（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },

    # === 新增：从 free-search-aggregator 集成的搜索引擎 ===
    "mojeek": {
        "module": "mojeek.mojeek_no_api",
        "function": "search_mojeek",
        "description": "Mojeek 独立索引搜索（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "duckduckgo_instant": {
        "module": "duckduckgo_instant.duckduckgo_instant",
        "function": "search_duckduckgo_instant",
        "description": "DuckDuckGo 即时答案（无需 API Key）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "no_api_key"
    },
    "exa": {
        "module": "exa.exa_search",
        "function": "search_exa",
        "description": "Exa AI 神经语义搜索（需 API Key，1000 次/月）",
        "default_limit": None,
        "requires_api_key": True,
        "group": "api_key"
    },
    "serper": {
        "module": "serper.serper_search",
        "function": "search_serper",
        "description": "Serper Google 搜索 API（需 API Key，2500 次/天）",
        "default_limit": None,
        "requires_api_key": True,
        "group": "api_key"
    },

    "firecrawl": {
        "module": "firecrawl.firecrawl_search",
        "function": "search_firecrawl",
        "description": "Firecrawl 搜索 API（需 API Key，支持网页正文抓取）",
        "default_limit": None,
        "requires_api_key": True,
        "group": "api_key"
    },
    "deepseek": {
        "module": "deepseek.deepseek_search",
        "function": "search_deepseek",
        "description": "DeepSeek 联网搜索 API（需 API Key，5 元/千次）",
        "default_limit": None,
        "requires_api_key": True,
        "group": "api_key"
    },
    "yuanbao": {
        "module": "yuanbao.yuanbao_search",
        "function": "search_yuanbao",
        "description": "腾讯元宝搜索（腾讯云联网搜索 API，需服务 API Key）",
        "default_limit": None,
        "requires_api_key": True,
        "group": "api_key"
    },
    "tinyfish": {
        "module": "tinyfish.tinyfish_search",
        "function": "search_tinyfish",
        "description": "TinyFish 搜索（需 API Key，免费额度）",
        "default_limit": None,
        "requires_api_key": True,
        "group": "api_key"
    },
    "anysearch": {
        "module": "anysearch.anysearch_search",
        "function": "search_anysearch",
        "description": "AnySearch 实时搜索（支持匿名访问，配 API Key 提高限额）",
        "default_limit": None,
        "requires_api_key": False,
        "group": "api_key"
    },
    "bailian": {
        "module": "bailian.bailian_search",
        "function": "search_bailian",
        "description": "阿里云百炼联网搜索（DashScope，需 API Key）",
        "default_limit": None,
        "requires_api_key": True,
        "group": "api_key"
    },
    "zhihu_official": {
        "module": "zhihu_official.zhihu_official_search",
        "function": "search_zhihu_official",
        "description": "知乎开放平台搜索（站内搜索，需 Access Secret）",
        "default_limit": None,
        "requires_api_key": True,
        "group": "api_key"
    },
    "parallel": {
        "module": "parallel_search.parallel_search",
        "function": "search_parallel",
        "description": "Parallel Search（自然语言目标与摘录，需 API Key）",
        "default_limit": None,
        "requires_api_key": True,
        "group": "api_key"
    },
    "ollama": {
        "module": "ollama_search.ollama_search",
        "function": "search_ollama",
        "description": "Ollama Web Search（托管网页搜索，需 API Key）",
        "default_limit": None,
        "requires_api_key": True,
        "group": "api_key"
    },
    "zhipu": {
        "module": "zhipu.zhipu_search",
        "function": "search_zhipu",
        "description": "智谱网络搜索（基础、高级、搜狗、夸克，需 API Key）",
        "default_limit": None,
        "requires_api_key": True,
        "group": "api_key"
    },
    "kimi": {
        "module": "kimi.kimi_search",
        "function": "search_kimi",
        "description": "Kimi 独立搜索（基础与专业，需 API Key）",
        "default_limit": None,
        "requires_api_key": True,
        "group": "api_key"
    },


    "claude_code": {
        "module": "ai_tools.adapter",
        "function": "search",
        "description": "Claude Code 原生 WebSearch（本机登录与账号额度）",
        "default_limit": None,
    },
    "codex": {
        "module": "ai_tools.adapter",
        "function": "search",
        "description": "Codex 账号原生搜索（本机 OAuth 登录）",
        "default_limit": None,
    },
    "grok_build": {
        "module": "ai_tools.adapter",
        "function": "search",
        "description": "Grok Build 原生 web_search（本机登录与账号额度）",
        "default_limit": None,
    },
    "defuddle": {
        "module": "url_to_markdown.engines.defuddle.defuddle_cli",
        "function": "url_to_markdown",
        "description": "Defuddle 网页内容提取（免费无限制）",
        "default_limit": None
    },
}

# 平台分组
# Shared credential metadata keeps grouping consistent with CLI discovery and doctor.
from .platform_metadata import REQUIRED_ENV, LOCAL_ACCOUNT_PLATFORMS

_TOOL_PLATFORMS = ["defuddle"]
_SEARCH_PLATFORMS = [name for name in PLATFORM_MODULES if name not in _TOOL_PLATFORMS]
_GENERAL_PLATFORMS = [name for name in _SEARCH_PLATFORMS if not REQUIRED_ENV.get(name) and name not in LOCAL_ACCOUNT_PLATFORMS]
_API_PLATFORMS = [name for name in _SEARCH_PLATFORMS if REQUIRED_ENV.get(name)]

PLATFORM_GROUPS = {
    "general": list(_GENERAL_PLATFORMS),
    "api": list(_API_PLATFORMS),
    "ai_tools": list(LOCAL_ACCOUNT_PLATFORMS),
    # Compatibility aliases. Search no longer mixes credential-free and API channels.
    "no_api_key": list(_GENERAL_PLATFORMS),
    "search": list(_GENERAL_PLATFORMS),
    # Topic groups are independent of credential groups.
    "dev": ["github", "reddit"],
    "social": ["youtube", "zhihu_official", "xiaoyuzhoufm"],
    "preferred": ["baidu_direct", "so360_direct", "sogou_direct", "duckduckgo_html", "startpage_direct", "brave_direct"],
    "tools": list(_TOOL_PLATFORMS),
    "all": list(_SEARCH_PLATFORMS),
}


# 无 API Key 直连平台脚本映射（与 scripts/channels/*/*_no_api.py 对齐）
DIRECT_NO_API_SCRIPT_MAP: Dict[str, Tuple[str, str]] = {
    "baidu_direct": ("baidu", "baidu_no_api.py"),
    "bing_cn_direct": ("bing", "bing_cn_no_api.py"),
    "bing_int_direct": ("bing", "bing_int_no_api.py"),
    "so360_direct": ("so360", "so360_no_api.py"),
    "sogou_direct": ("sogou", "sogou_no_api.py"),
    "toutiao_direct": ("toutiao", "toutiao_no_api.py"),
    "jisilu_direct": ("jisilu", "jisilu_no_api.py"),
    "google_direct": ("google_search", "google_no_api.py"),
    "google_hk_direct": ("google_search", "google_hk_no_api.py"),
    "duckduckgo_html": ("duckduckgo", "duckduckgo_no_api.py"),
    "startpage_direct": ("startpage", "startpage_no_api.py"),
    "brave_direct": ("brave", "brave_no_api.py"),
    "yahoo_direct": ("yahoo", "yahoo_no_api.py"),
    "ecosia_direct": ("ecosia", "ecosia_no_api.py"),
    "qwant_direct": ("qwant", "qwant_no_api.py"),
    "wolfram_direct": ("wolfram", "wolfram_no_api.py"),
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
    existing_keys = set(os.environ)
    load_dotenv(env_file, override=False, encoding="utf-8")
    loaded_count = len(set(os.environ) - existing_keys)

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
        if platform in LOCAL_ACCOUNT_PLATFORMS:
            from ai_tools.adapter import search as native_search
            result["items"] = native_search(platform, keyword, limit, **kwargs)
        elif platform == "github":
            result["items"] = _search_github(keyword, limit, **kwargs)
        elif platform == "reddit":
            result["items"] = _search_reddit(keyword, limit, **kwargs)
        elif platform == "youtube":
            result["items"] = _search_youtube(keyword, limit, **kwargs)
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
        elif platform == "mojeek":
            result["items"] = _search_mojeek(keyword, limit, **kwargs)
        elif platform == "duckduckgo_instant":
            result["items"] = _search_duckduckgo_instant(keyword, limit, **kwargs)
        elif platform == "exa":
            result["items"] = _search_exa(keyword, limit, **kwargs)
        elif platform == "serper":
            result["items"] = _search_serper(keyword, limit, **kwargs)
        elif platform == "firecrawl":
            result["items"] = _search_firecrawl(keyword, limit, **kwargs)
        elif platform == "deepseek":
            result["items"] = _search_deepseek(keyword, limit, **kwargs)
        elif platform == "yuanbao":
            result["items"] = _search_yuanbao(keyword, limit, **kwargs)
        elif platform == "tinyfish":
            result["items"] = _search_tinyfish(keyword, limit, **kwargs)
        elif platform == "anysearch":
            result["items"] = _search_anysearch(keyword, limit, **kwargs)
        elif platform == "bailian":
            result["items"] = _search_bailian(keyword, limit, **kwargs)
        elif platform == "zhihu_official":
            result["items"] = _search_zhihu_official(keyword, limit, **kwargs)
        elif platform == "parallel":
            result["items"] = _search_parallel(keyword, limit, **kwargs)
        elif platform == "ollama":
            result["items"] = _search_ollama(keyword, limit, **kwargs)
        elif platform == "zhipu":
            result["items"] = _search_zhipu(keyword, limit, **kwargs)
        elif platform == "kimi":
            result["items"] = _search_kimi(keyword, limit, **kwargs)
        elif platform in DIRECT_NO_API_SCRIPT_MAP:
            result["items"] = _search_no_api_direct(platform, keyword, limit, **kwargs)
        elif platform == "defuddle":
            result["items"] = _search_defuddle(keyword, limit, **kwargs)
        else:
            result["error"] = f"Unknown platform: {platform}"
            logger.error(result["error"])
            return platform, result

        result["total"] = len(result["items"])

        # 区分真正的成功（有线结果）和空结果
        if result["total"] > 0:
            result["success"] = True
            result["has_results"] = True
        else:
            # 空结果可能是因为：没有匹配内容、API 限流、网络问题等
            result["success"] = True  # 命令执行成功
            result["has_results"] = False  # 但没有返回结果
            result["warning"] = "No results returned (may indicate API rate limit or network issue)"

        elapsed = (datetime.now() - start_time).total_seconds()
        result["timing_ms"] = int(elapsed * 1000)

        if result["total"] > 0:
            logger.info(f"平台 {platform} 搜索完成: {result['total']} 条结果, 耗时 {elapsed:.2f}s")
        else:
            logger.warning(f"平台 {platform} 搜索完成: 0 条结果, 耗时 {elapsed:.2f}s")

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
    script_path = CHANNELS_DIR / "github_search" / "github_search.py"
    cmd = [sys.executable, str(script_path), "repo", keyword, "--format", "json"]
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="github")
    items = data.get("items", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_reddit(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Reddit 搜索"""
    script_path = CHANNELS_DIR / "reddit" / "cli.py"
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


def _search_youtube(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """YouTube 搜索"""
    script_path = CHANNELS_DIR / "youtube" / "youtube_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    data = _run_platform_json_command(cmd, timeout=60, platform="youtube")
    if not isinstance(data, list):
        return []
    return data[:limit] if limit is not None else data


def _search_google(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Google 搜索"""
    script_path = CHANNELS_DIR / "google_search" / "google_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-n", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="google")
    items = data.get("items", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_tavily(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Tavily AI 搜索"""
    script_path = CHANNELS_DIR / "tavily_search" / "tavily_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["--max-results", str(limit)])
    data = _run_platform_json_command(cmd, timeout=60, platform="tavily")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_jina(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Jina AI 搜索"""
    script_path = CHANNELS_DIR / "jina" / "jina_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    data = _run_platform_json_command(cmd, timeout=60, platform="jina")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_duckduckgo(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """DuckDuckGo 搜索"""
    script_path = CHANNELS_DIR / "duckduckgo" / "duckduckgo_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="duckduckgo")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_brave(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Brave 搜索"""
    script_path = CHANNELS_DIR / "brave" / "brave_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="brave")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_yahoo(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Yahoo 搜索"""
    script_path = CHANNELS_DIR / "yahoo" / "yahoo_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="yahoo")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_yandex(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Yandex 搜索"""
    script_path = CHANNELS_DIR / "yandex" / "yandex_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    # 不在这里手动固定单个 key，交由 yandex_search.py 内部做多 key 轮换
    data = _run_platform_json_command(cmd, timeout=30, platform="yandex")
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_bing(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Bing 搜索"""
    # 收集所有 SerpAPI key 传递给子进程（bing会自动读取SERPAPI_API_KEY*环境变量）
    serpapi_env = {k: v for k, v in os.environ.items() if k.startswith("SERPAPI_API_KEY") and v}

    script_path = CHANNELS_DIR / "bing" / "bing_serpapi_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    data = _run_platform_json_command(cmd, timeout=30, platform="bing", env=serpapi_env if serpapi_env else None)
    items = data.get("results", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_wikipedia(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Wikipedia 搜索"""
    script_path = CHANNELS_DIR / "wikipedia" / "wikipedia_search.py"
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
    script_path = CHANNELS_DIR / "metaso" / "metaso_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--format", "json", "--summary"]
    if limit is not None:
        cmd.extend(["--size", str(limit)])
    data = _run_platform_json_command(cmd, timeout=60, platform="metaso")
    items = data.get("webpages", [])
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_volcengine(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """火山引擎搜索"""
    script_path = CHANNELS_DIR / "volcengine" / "volcengine_search.py"
    version = os.getenv("VOLCENGINE_SEARCH_VERSION", "custom").strip().lower()
    if version not in ("global", "custom"):
        raise ValueError("VOLCENGINE_SEARCH_VERSION 仅支持 global 或 custom")
    search_type = "web" if version == "global" else "summary"
    cmd = [sys.executable, str(script_path), "--version", version, search_type, keyword]
    if limit is not None:
        count = min(limit, 20) if version == "global" else limit
        cmd.extend(["--count", str(count)])
    data = _run_platform_json_command(cmd, timeout=60, platform="volcengine")
    if isinstance(data, dict) and data.get("error"):
        raise Exception(str(data.get("error")))
    items: Any = []
    if isinstance(data, dict):
        result_obj = data.get("Result")
        if isinstance(result_obj, dict):
            field = "Documents" if version == "global" else "WebResults"
            items = result_obj.get(field, [])
        elif version == "custom":
            items = data.get("Data", {}).get("SearchResults", [])
    if not isinstance(items, list):
        raise TypeError("Volcengine 搜索结果必须为列表")

    excluded_fields = {"Content", "LogoUrl"}
    sanitized_items: List[Dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            sanitized = {k: v for k, v in item.items() if k not in excluded_fields}
            if version == "global":
                sanitized["title"] = item.get("Title", "")
                sanitized["url"] = item.get("Url", "")
                sanitized["Snippet"] = "\n".join(
                    snippet["Text"]
                    for snippet in item.get("Snippet", [])
                    if snippet.get("Type") == "text" and snippet.get("Text")
                )
            sanitized_items.append(sanitized)

    return sanitized_items[:limit] if limit is not None else sanitized_items


def _search_baidu(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """百度千帆搜索"""
    script_path = CHANNELS_DIR / "baidu" / "baidu_search.py"
    payload: Dict[str, Any] = {"query": keyword}
    if limit is not None:
        payload["count"] = limit
    freshness = kwargs.get("freshness")
    if freshness:
        payload["freshness"] = freshness

    cmd = [sys.executable, str(script_path), json.dumps(payload, ensure_ascii=False)]

    env: Dict[str, str] = {}
    explicit_api_key = kwargs.get("api_key")
    if explicit_api_key:
        env["BAIDU_API_KEY"] = str(explicit_api_key)
    elif os.getenv("BAIDU_QIANFAN_API_KEY") and not os.getenv("BAIDU_API_KEY"):
        # 兼容旧配置，自动映射到新脚本读取的变量名。
        env["BAIDU_API_KEY"] = os.getenv("BAIDU_QIANFAN_API_KEY", "")

    data = _run_platform_json_command(
        cmd,
        timeout=30,
        platform="baidu",
        env=env or None,
    )

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("results", []) or data.get("references", [])
    else:
        items = []
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_no_api_direct(platform: str, keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """统一执行 *_direct 无 API Key 平台脚本。"""
    script_parts = DIRECT_NO_API_SCRIPT_MAP.get(platform)
    if not script_parts:
        raise Exception(f"Unsupported no-api platform: {platform}")

    script_path = CHANNELS_DIR.joinpath(*script_parts)
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])

    proxy = kwargs.get("proxy")
    if proxy:
        cmd.extend(["--proxy", str(proxy)])

    timeout = int(kwargs.get("timeout", 45))
    data = _run_platform_json_command(cmd, timeout=timeout, platform=platform)
    items = data.get("results", []) if isinstance(data, dict) else []
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_defuddle(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Defuddle 平台：将 URL 提取为 Markdown 内容。"""
    url = keyword.strip()
    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        raise Exception("defuddle requires a valid URL (http/https)")

    from url_to_markdown.engines.defuddle_engine import DefuddleEngine

    timeout = int(kwargs.get("timeout", 60))
    engine = DefuddleEngine(timeout=timeout)
    data = engine.fetch(url=url, markdown=True, json_output=True, timeout=timeout)
    item = {
        "title": data.get("title", "") or url,
        "url": data.get("url", url),
        "description": data.get("description", ""),
        "content": data.get("content", ""),
    }
    return [item]


def _search_xiaoyuzhoufm(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:

    """小宇宙FM播客搜索"""
    script_path = CHANNELS_DIR / "xiaoyuzhoufm" / "xiaoyuzhou_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["--size", str(limit)])
    data = _run_platform_json_command(cmd, timeout=60, platform="xiaoyuzhoufm")
    items = data.get("podcasts", []) if isinstance(data, dict) else []
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_mojeek(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Mojeek 搜索 - 独立索引，无需 API Key"""
    script_path = CHANNELS_DIR / "mojeek" / "mojeek_no_api.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])

    proxy = kwargs.get("proxy")
    if proxy:
        cmd.extend(["--proxy", str(proxy)])

    timeout = int(kwargs.get("timeout", 30))
    data = _run_platform_json_command(cmd, timeout=timeout, platform="mojeek")
    items = data.get("results", []) if isinstance(data, dict) else []
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_duckduckgo_instant(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """DuckDuckGo Instant Answer - 即时答案，无需 API Key"""
    script_path = CHANNELS_DIR / "duckduckgo_instant" / "duckduckgo_instant.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])

    proxy = kwargs.get("proxy")
    if proxy:
        cmd.extend(["--proxy", str(proxy)])

    timeout = int(kwargs.get("timeout", 30))
    data = _run_platform_json_command(cmd, timeout=timeout, platform="duckduckgo_instant")
    items = data.get("results", []) if isinstance(data, dict) else []
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_exa(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Exa AI 神经语义搜索 - 需要 EXA_API_KEY"""
    script_path = CHANNELS_DIR / "exa" / "exa_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])

    # 传递 API Key
    env = {}
    api_key = kwargs.get("api_key") or os.environ.get("EXA_API_KEY")
    if api_key:
        env["EXA_API_KEY"] = api_key

    search_type = kwargs.get("search_type", "auto")
    cmd.extend(["--type", search_type])

    timeout = int(kwargs.get("timeout", 30))
    data = _run_platform_json_command(cmd, timeout=timeout, platform="exa", env=env or None)
    items = data.get("results", []) if isinstance(data, dict) else []
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_serper(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Serper Google 搜索 API - 需要 SERPER_API_KEY"""
    script_path = CHANNELS_DIR / "serper" / "serper_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])

    # 传递 API Key
    env = {}
    api_key = kwargs.get("api_key") or os.environ.get("SERPER_API_KEY")
    if api_key:
        env["SERPER_API_KEY"] = api_key

    page = kwargs.get("page", 1)
    gl = kwargs.get("gl", "us")
    hl = kwargs.get("hl", "en")
    location = kwargs.get("location")

    if page != 1:
        cmd.extend(["--page", str(page)])
    cmd.extend(["--gl", gl])
    cmd.extend(["--hl", hl])
    if location:
        cmd.extend(["--location", location])

    timeout = int(kwargs.get("timeout", 30))
    data = _run_platform_json_command(cmd, timeout=timeout, platform="serper", env=env or None)
    items = data.get("results", []) if isinstance(data, dict) else []
    return items[:limit] if isinstance(items, list) and limit is not None else (items if isinstance(items, list) else [])


def _search_firecrawl(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Firecrawl 搜索"""
    script_path = CHANNELS_DIR / "firecrawl" / "firecrawl_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    for name in ("sources", "categories", "include_domains", "exclude_domains", "formats"):
        if kwargs.get(name):
            cmd.append("--" + name.replace("_", "-"))
            cmd.extend(str(value) for value in kwargs[name])
    for name in ("tbs", "location", "country", "api_url"):
        if kwargs.get(name) is not None:
            cmd.extend(["--" + name.replace("_", "-"), str(kwargs[name])])
    if kwargs.get("scrape"):
        cmd.append("--scrape")
    env = {"FIRECRAWL_API_KEY": str(kwargs["api_key"])} if kwargs.get("api_key") else None
    timeout = int(kwargs.get("timeout", 60))
    cmd.extend(["--timeout", str(timeout)])
    data = _run_platform_json_command(cmd, timeout=timeout + 10, platform="firecrawl", env=env)
    items = data["results"]
    return items[:limit] if limit is not None else items


def _search_deepseek(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """DeepSeek 联网搜索"""
    script_path = CHANNELS_DIR / "deepseek" / "deepseek_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    for name in ("ori_question", "localization", "api_url"):
        if kwargs.get(name) is not None:
            cmd.extend(["--" + name.replace("_", "-"), str(kwargs[name])])
    if kwargs.get("need_content"):
        cmd.append("--need-content")
    env = {"DEEPSEEK_API_KEY": str(kwargs["api_key"])} if kwargs.get("api_key") else None
    timeout = int(kwargs.get("timeout", 30))
    cmd.extend(["--timeout", str(timeout)])
    data = _run_platform_json_command(cmd, timeout=timeout + 10, platform="deepseek", env=env)
    items = data["results"]
    return items[:limit] if limit is not None else items


def _search_yuanbao(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """腾讯元宝搜索"""
    script_path = CHANNELS_DIR / "yuanbao" / "yuanbao_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    for name in ("mode", "site", "industry", "freshness", "endpoint"):
        if kwargs.get(name) is not None:
            cmd.extend(["--" + name, str(kwargs[name])])
    if kwargs.get("deeplinks"):
        cmd.append("--deeplinks")
    env = {"TENCENTCLOUD_WSA_APIKEY": str(kwargs["api_key"])} if kwargs.get("api_key") else None
    timeout = int(kwargs.get("timeout", 30))
    cmd.extend(["--timeout", str(timeout)])
    data = _run_platform_json_command(cmd, timeout=timeout + 10, platform="yuanbao", env=env)
    items = data["results"]
    return items[:limit] if limit is not None else items


def _search_tinyfish(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """TinyFish 搜索"""
    script_path = CHANNELS_DIR / "tinyfish" / "tinyfish_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    for name in ("location", "language", "endpoint"):
        if kwargs.get(name) is not None:
            cmd.extend(["--" + name, str(kwargs[name])])
    env = {"TINYFISH_API_KEY": str(kwargs["api_key"])} if kwargs.get("api_key") else None
    timeout = int(kwargs.get("timeout", 15))
    cmd.extend(["--timeout", str(timeout)])
    data = _run_platform_json_command(cmd, timeout=timeout + 10, platform="tinyfish", env=env)
    items = data["results"]
    return items[:limit] if limit is not None else items


def _search_bailian(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """阿里云百炼联网搜索"""
    script_path = CHANNELS_DIR / "bailian" / "bailian_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    for name in ("model", "strategy", "freshness", "endpoint"):
        if kwargs.get(name) is not None:
            cmd.extend(["--" + name, str(kwargs[name])])
    if kwargs.get("sites"):
        cmd.append("--sites")
        cmd.extend(str(value) for value in kwargs["sites"])
    if kwargs.get("vertical"):
        cmd.append("--vertical")
    env = {"DASHSCOPE_API_KEY": str(kwargs["api_key"])} if kwargs.get("api_key") else None
    timeout = int(kwargs.get("timeout", 60))
    cmd.extend(["--timeout", str(timeout)])
    data = _run_platform_json_command(cmd, timeout=timeout + 10, platform="bailian", env=env)
    items = data["results"]
    return items[:limit] if limit is not None else items


def _search_zhihu_official(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """知乎开放平台搜索"""
    scope = kwargs.get("scope", "search")
    if scope not in ("search", "global"):
        raise ValueError("scope 只能是 search 或 global")
    script_path = CHANNELS_DIR / "zhihu_official" / "zhihu_official_search.py"
    cmd = [sys.executable, str(script_path), scope, keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    if kwargs.get("base_url") is not None:
        cmd.extend(["--base-url", str(kwargs["base_url"])])
    access_secret = kwargs.get("access_secret") or kwargs.get("api_key")
    env = {"ZHIHU_ACCESS_SECRET": str(access_secret)} if access_secret else None
    timeout = int(kwargs.get("timeout", 10))
    cmd.extend(["--timeout", str(timeout)])
    data = _run_platform_json_command(cmd, timeout=timeout + 10, platform="zhihu_official", env=env)
    items = data["results"]
    return items[:limit] if limit is not None else items


def _search_parallel(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Parallel Search"""
    script_path = CHANNELS_DIR / "parallel_search" / "parallel_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    for name in ("objective", "mode", "location", "after_date", "endpoint"):
        if kwargs.get(name) is not None:
            cmd.extend(["--" + name.replace("_", "-"), str(kwargs[name])])
    for name, option in (("search_queries", "--search-query"), ("include_domains", "--include-domain"), ("exclude_domains", "--exclude-domain")):
        for value in kwargs.get(name) or []:
            cmd.extend([option, str(value)])
    env = {"PARALLEL_API_KEY": str(kwargs["api_key"])} if kwargs.get("api_key") else None
    timeout = int(kwargs.get("timeout", 30))
    cmd.extend(["--timeout", str(timeout)])
    data = _run_platform_json_command(cmd, timeout=timeout + 10, platform="parallel", env=env)
    items = data["results"]
    return items[:limit] if limit is not None else items


def _search_ollama(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Ollama Web Search"""
    script_path = CHANNELS_DIR / "ollama_search" / "ollama_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    if kwargs.get("endpoint") is not None:
        cmd.extend(["--endpoint", str(kwargs["endpoint"])])
    env = {"OLLAMA_API_KEY": str(kwargs["api_key"])} if kwargs.get("api_key") else None
    timeout = int(kwargs.get("timeout", 30))
    cmd.extend(["--timeout", str(timeout)])
    data = _run_platform_json_command(cmd, timeout=timeout + 10, platform="ollama", env=env)
    items = data["results"]
    return items[:limit] if limit is not None else items


def _search_zhipu(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """智谱网络搜索"""
    script_path = CHANNELS_DIR / "zhipu" / "zhipu_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    search_engine = kwargs.get("search_engine") or kwargs.get("engine")
    if search_engine is not None:
        cmd.extend(["--engine", str(search_engine)])
    for name in ("domain", "recency", "content_size", "endpoint"):
        if kwargs.get(name) is not None:
            cmd.extend(["--" + name.replace("_", "-"), str(kwargs[name])])
    if kwargs.get("search_intent"):
        cmd.append("--search-intent")
    env = {"ZHIPU_API_KEY": str(kwargs["api_key"])} if kwargs.get("api_key") else None
    timeout = int(kwargs.get("timeout", 30))
    cmd.extend(["--timeout", str(timeout)])
    data = _run_platform_json_command(cmd, timeout=timeout + 10, platform="zhipu", env=env)
    items = data["results"]
    return items[:limit] if limit is not None else items


def _search_kimi(keyword: str, limit: Optional[int], **kwargs) -> List[Dict]:
    """Kimi 独立搜索"""
    script_path = CHANNELS_DIR / "kimi" / "kimi_search.py"
    cmd = [sys.executable, str(script_path), keyword, "--json"]
    if limit is not None:
        cmd.extend(["-m", str(limit)])
    for name in ("tier", "start", "end", "base_url"):
        if kwargs.get(name) is not None:
            cmd.extend(["--" + name.replace("_", "-"), str(kwargs[name])])
    for site in kwargs.get("sites") or []:
        cmd.extend(["--site", str(site)])
    if kwargs.get("include_content"):
        cmd.append("--include-content")
    env = {"MOONSHOT_API_KEY": str(kwargs["api_key"])} if kwargs.get("api_key") else None
    timeout = int(kwargs.get("timeout", 30))
    cmd.extend(["--timeout", str(timeout)])
    data = _run_platform_json_command(cmd, timeout=timeout + 10, platform="kimi", env=env)
    items = data["results"]
    return items[:limit] if limit is not None else items


# =============================================================================
# 并发搜索
# =============================================================================

def union_search(
    keyword: str,
    platforms: List[str],
    limit: Optional[int] = None,
    max_workers: int = 5,
    timeout: int = 60,
    deduplicate: bool = False,
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
            "total_items": 0,
            "raw_total_items": 0,
            "deduplicated_total_items": 0,
            "deduplicated_removed": 0,
            "deduplicate_enabled": deduplicate
        },
        "final_items": []
    }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(search_platform, platform, keyword, limit, timeout=timeout, **kwargs): platform
            for platform in platforms
        }

        completed = 0
        completed_futures = set()
        try:
            for future in as_completed(futures, timeout=timeout):
                platform = futures[future]
                completed += 1
                completed_futures.add(future)

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
        except FuturesTimeoutError:
            logger.error(f"并发搜索达到超时时间 {timeout}s，部分平台未完成")

        # 将超时未完成的平台标记为失败，避免直接抛异常导致整个命令退出
        for future, platform in futures.items():
            if future in completed_futures:
                continue
            future.cancel()
            if platform in results["results"]:
                continue
            results["results"][platform] = {
                "platform": platform,
                "success": False,
                "error": f"Timed out after {timeout}s",
                "items": [],
                "total": 0,
                "timing_ms": timeout * 1000,
            }
            results["summary"]["failed"] += 1
            logger.warning(f"[timeout] {platform}: 未在 {timeout}s 内完成")

    # 聚合成功平台条目，输出统一结果视图（可选去重）
    merged_items: List[Dict[str, Any]] = []
    for platform, platform_result in results["results"].items():
        if not platform_result.get("success"):
            continue
        for item in platform_result.get("items", []):
            if isinstance(item, dict):
                merged_item = dict(item)
                merged_item["_source_platform"] = platform
                merged_items.append(merged_item)

    raw_total = len(merged_items)
    results["summary"]["raw_total_items"] = raw_total

    if deduplicate:
        final_items, removed = _deduplicate_items(merged_items)
        dedup_total = len(final_items)
        results["summary"]["deduplicated_total_items"] = dedup_total
        results["summary"]["deduplicated_removed"] = removed
        results["summary"]["total_items"] = dedup_total
        results["final_items"] = final_items
    else:
        results["summary"]["deduplicated_total_items"] = raw_total
        results["summary"]["deduplicated_removed"] = 0
        results["summary"]["total_items"] = raw_total
        results["final_items"] = merged_items

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

  # URL转Markdown
  python union_search.py --read-url "https://example.com"
  python union_search.py --read-url "https://github.com" --read-timeout 60 --json
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
        "--deduplicate",
        action="store_true",
        help="启用跨平台结果去重（按标题或链接）"
    )
    parser.add_argument(
        "--read-url",
        metavar="URL",
        help="将指定URL转换为Markdown内容（基于Jina AI Reader API）"
    )
    parser.add_argument(
        "--read-timeout",
        type=int,
        default=30,
        help="URL读取超时时间（秒，默认: 30）"
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

    print("\n## 平台组")
    for group, platforms in PLATFORM_GROUPS.items():
        print(f"- {group}: {', '.join(platforms)}")


def main():
    """主函数"""
    args = parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
        logger.info("启用详细日志模式")
    else:
        logging.getLogger().setLevel(logging.ERROR)

    # 初始化搜索日志记录器
    search_logger = SearchLogger(verbose=args.verbose)

    # 列出平台
    if args.list_platforms:
        list_platforms()
        return 0

    # URL转Markdown功能
    if args.read_url:
        if not URL_TO_MARKDOWN_AVAILABLE:
            print("错误: url_to_markdown模块未安装", file=sys.stderr)
            return 1

        load_env_file(args.env_file)

        print(f"正在读取URL: {args.read_url}", file=sys.stderr)

        try:
            client = UrlToMarkdown(timeout=args.read_timeout)
            result = client.fetch(args.read_url)

            if args.json:
                output = {
                    "url": result["url"],
                    "title": result.get("title", ""),
                    "content": result["content"],
                }
                if args.pretty:
                    print(json.dumps(output, indent=2, ensure_ascii=False))
                else:
                    print(json.dumps(output, ensure_ascii=False))
            else:
                # Markdown格式输出
                if result.get("title"):
                    print(f"# {result['title']}")
                    print("")
                if result.get("url"):
                    print(f"**Source**: {result['url']}")
                    print("")
                print("---")
                print("")
                print(result["content"])

            return 0
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            return 1

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
        # 默认只搜索无需必填 API Key 的渠道
        platforms = PLATFORM_GROUPS["general"]

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
        timeout=args.timeout,
        deduplicate=args.deduplicate
    )
    elapsed = (datetime.now() - start_time).total_seconds()

    logger.info(f"搜索完成: 总耗时 {elapsed:.2f}s, 成功 {results['summary']['successful']}/{len(platforms)}")

    # 构建详细日志元数据
    metadata = {
        "response_time": elapsed,
        "status": "success" if results["summary"]["successful"] > 0 else "failed",
        "total_platforms": results["summary"]["total_platforms"],
        "successful_platforms": results["summary"]["successful"],
        "failed_platforms": results["summary"]["failed"],
        "total_items": results["summary"]["total_items"],
        "platform_details": [
            {
                "platform": platform,
                "status": "success" if result.get("success") else "failed",
                "items": result.get("total", 0),
                "timing_ms": result.get("timing_ms", 0),
                "error": result.get("error")
            }
            for platform, result in results["results"].items()
        ],
    }

    # 记录搜索日志
    log_filepath = search_logger.log_union_search(
        query=args.keyword,
        results=results["final_items"],
        metadata=metadata
    )
    logger.info(f"搜索日志已保存到: {log_filepath}")

    # 格式化输出
    if args.json or (args.output and args.output.endswith(".json")):
        output = format_json(results, pretty=args.pretty)
    else:
        output = format_markdown(results)

    # 输出结果
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = Path(__file__).parent / output_path
        write_text_atomic(str(output_path), output)
        print(f"\n结果已保存到: {output_path}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
