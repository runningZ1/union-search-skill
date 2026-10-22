"""Shared credential and status metadata for grouping and CLI discovery."""

from typing import Dict, Tuple

REQUIRED_ENV: Dict[str, Tuple[str, ...]] = {
    "google": ("GOOGLE_API_KEY", "GOOGLE_SEARCH_ENGINE_ID"),
    "tavily": ("TAVILY_API_KEY",),
    "jina": ("JINA_API_KEY",),
    "yandex": ("SERPAPI_API_KEY",),
    "bing": ("SERPAPI_API_KEY",),
    "metaso": ("METASO_API_KEY",),
    "volcengine": ("VOLCENGINE_API_KEY",),
    "baidu": ("BAIDU_API_KEY",),
    "youtube": ("YOUTUBE_API_KEY",),
    "firecrawl": ("FIRECRAWL_API_KEY",),
    "deepseek": ("DEEPSEEK_API_KEY",),
    "yuanbao": ("TENCENTCLOUD_WSA_APIKEY",),
    "tinyfish": ("TINYFISH_API_KEY",),
    "bailian": ("DASHSCOPE_API_KEY",),
    "zhihu_official": ("ZHIHU_ACCESS_SECRET",),
    "cloudflare": ("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"),
    "parallel": ("PARALLEL_API_KEY",),
    "querit": ("QUERIT_API_KEY",),
    "ollama": ("OLLAMA_API_KEY",),
    "zhipu": ("ZHIPU_API_KEY",),
    "kimi": ("MOONSHOT_API_KEY",),
    "exa": ("EXA_API_KEY",),
    "serper": ("SERPER_API_KEY",),
    "xiaoyuzhoufm": ("METASO_API_KEY",),
    # Defuddle requires Node.js but no API key
}

OPTIONAL_ENV: Dict[str, Tuple[str, ...]] = {
    "github": ("GITHUB_TOKEN",),
    "duckduckgo": ("DUCKDUCKGO_PROXY",),
    "brave": ("BRAVE_PROXY",),
    "yahoo": ("YAHOO_PROXY",),
    "wikipedia": ("WIKIPEDIA_PROXY",),
    "baidu": ("BAIDU_QIANFAN_API_KEY",),
    "anysearch": ("ANYSEARCH_API_KEY",),
}

STATUS: Dict[str, str] = {
    "reddit": "degraded",
    "volcengine": "degraded",
}

NOTES: Dict[str, str] = {
    "reddit": "May hit 403 depending on source endpoint and IP.",
    "volcengine": "Historically had response parsing instability.",
    "anysearch": "Works without a key at lower rate limits.",
}

