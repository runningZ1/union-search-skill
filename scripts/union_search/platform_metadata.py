"""Shared credential and status metadata for grouping and CLI discovery."""

from typing import Dict, Tuple

LOCAL_ACCOUNT_PLATFORMS = ("claude_code", "codex", "grok_build")

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
    "parallel": ("PARALLEL_API_KEY",),
    "ollama": ("OLLAMA_API_KEY",),
    "zhipu": ("ZHIPU_API_KEY",),
    "kimi": ("MOONSHOT_API_KEY",),
    "exa": ("EXA_API_KEY",),
    "serper": ("SERPER_API_KEY",),
    "xiaoyuzhoufm": ("METASO_API_KEY",),
    "anysearch": ("ANYSEARCH_API_KEY",),
    # Defuddle requires Node.js but no API key
}

OPTIONAL_ENV: Dict[str, Tuple[str, ...]] = {
    "github": ("GITHUB_TOKEN",),
    "duckduckgo": ("DUCKDUCKGO_PROXY",),
    "brave": ("BRAVE_PROXY",),
    "yahoo": ("YAHOO_PROXY",),
    "wikipedia": ("WIKIPEDIA_PROXY",),
    "baidu": ("BAIDU_QIANFAN_API_KEY",),
}

STATUS: Dict[str, str] = {
    "volcengine": "degraded",
    "quark_direct": "degraded",
}

NOTES: Dict[str, str] = {
    "claude_code": "Bundled Claude Code WebSearch; local CLI login and account quota required.",
    "codex": "Bundled Codex account search endpoint; local OAuth login required; endpoint is unofficial.",
    "grok_build": "Bundled Grok Build native web_search; local CLI login and quota required.",
    "volcengine": "Historically had response parsing instability.",
    "anysearch": "Requires ANYSEARCH_API_KEY.",
    "quark_direct": "Anonymous web search; may return CAPTCHA. No automatic retries or source switching.",
    "bing": "SerpAPI access; accepts any nonempty SERPAPI_API_KEY* variable. Separate from Bing web channels.",
    "yandex": "SerpAPI access; accepts any nonempty SERPAPI_API_KEY* variable. Separate from yandex_direct.",
    "yandex_direct": "Anonymous web search; separate from the SerpAPI channel.",
    "duckduckgo_html": "Compatibility name for duckduckgo; uses the same web implementation.",
    "brave_direct": "Compatibility name for brave; uses the same web implementation.",
    "yahoo_direct": "Compatibility name for yahoo; uses the same web implementation.",
}

