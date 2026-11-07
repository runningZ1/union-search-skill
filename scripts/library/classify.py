import json
import re
from urllib.parse import urlsplit

from lxml import html as lxml_html

CONTENT_TYPES = ("article", "listing", "video", "podcast", "pdf", "other", "unknown")
RESTRICTION_KINDS = ("paywall", "login", "captcha", "permission_denied", "region_blocked", "suspected", "unknown")

# 渠道本身只返回媒体条目
PLATFORM_TYPES = {"youtube": "video", "xiaoyuzhoufm": "podcast"}

# 主机与路径共同确定的媒体页面；只匹配具体条目页，不匹配频道首页
MEDIA_URL_RULES = (
    ("video", "youtube.com", re.compile(r"^/(watch|shorts/|live/)")),
    ("video", "youtu.be", re.compile(r"^/[\w-]+")),
    ("video", "m.youtube.com", re.compile(r"^/watch")),
    ("video", "bilibili.com", re.compile(r"^/video/")),
    ("video", "b23.tv", re.compile(r"^/[\w-]+")),
    ("video", "vimeo.com", re.compile(r"^/\d+")),
    ("video", "douyin.com", re.compile(r"^/video/")),
    ("video", "ixigua.com", re.compile(r"^/\d+")),
    ("video", "v.qq.com", re.compile(r"^/x/")),
    ("video", "tiktok.com", re.compile(r"^/@[^/]+/video/")),
    ("podcast", "xiaoyuzhoufm.com", re.compile(r"^/episode/")),
    ("podcast", "podcasts.apple.com", re.compile(r"/id\d+")),
    ("podcast", "open.spotify.com", re.compile(r"^/episode/")),
    ("podcast", "ximalaya.com", re.compile(r"/sound/")),
    ("podcast", "lizhi.fm", re.compile(r"^/\d+/\d+")),
)

ARTICLE_SCHEMA_TYPES = {"article", "newsarticle", "blogposting", "report", "scholarlyarticle", "techarticle", "webpage"}
LISTING_SCHEMA_TYPES = {"product", "itemlist", "collectionpage", "searchresultspage", "offer", "aggregateoffer"}

CAPTCHA_SELECTORS = (
    "//*[contains(@class,'g-recaptcha') or contains(@class,'h-captcha') or contains(@class,'cf-turnstile') or contains(@class,'geetest')]",
    "//script[contains(@src,'challenges.cloudflare.com') or contains(@src,'/cdn-cgi/challenge-platform') or contains(@src,'recaptcha/api.js') or contains(@src,'hcaptcha.com') or contains(@src,'captcha-delivery.com')]",
    "//form[contains(@id,'challenge-form')]",
    "//*[@id='px-captcha' or @id='challenge-error-text' or @id='cf-challenge-running']",
    "//script[contains(text(),'_cf_chl_opt')]",
)
PHP_FATAL_LABELS = ("Fatal error", "Parse error")
CAPTCHA_TITLES = ("just a moment...", "attention required! | cloudflare", "安全验证", "验证码", "security check", "security verification")
# 只按完整的 class 名或 id 匹配；正文标题和引用生成的 id 不应命中
PAYWALL_TOKENS = ("paywall", "subscriber-only", "premium-content", "locked-content", "gateway-content", "paywall-container", "chargeWall")
PAYWALL_CLASS_SELECTOR = "//*[" + " or ".join(
    f"contains(concat(' ', normalize-space(@class), ' '), ' {token} ') or @id='{token}'" for token in PAYWALL_TOKENS) + "]"
LOGIN_PATH = re.compile(r"/(login|signin|sign-in|passport|account/login|auth)(/|$|\?)", re.I)
SHELL_CONTAINERS = "//div[@id='root' or @id='app' or @id='__next' or @id='__nuxt']"

# 抽取文本少于该字数时，才把页面结构信号视为空壳或登录墙
SHORT_BODY_CHARS = 200


def _host(url):
    host = (urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def guess_from_hit(url, platform):
    """搜索阶段按渠道和网址给出初步类型，抓取后再用响应证据修正。"""
    if platform in PLATFORM_TYPES:
        return PLATFORM_TYPES[platform], [f"search_platform:{platform}"]
    host = _host(url)
    path = urlsplit(url).path
    for kind, rule_host, pattern in MEDIA_URL_RULES:
        if (host == rule_host or host.endswith("." + rule_host)) and pattern.search(path):
            return kind, [f"url_pattern:{rule_host}"]
    if path.lower().endswith(".pdf"):
        return "pdf", ["url_extension:.pdf"]
    return "unknown", []


def type_from_response(mime):
    """响应头类型；返回 None 表示需要解析 HTML 再判断。"""
    mime = (mime or "").split(";")[0].strip().lower()
    if mime in ("text/html", "application/xhtml+xml", ""):
        return None
    if mime == "application/pdf":
        return "pdf"
    if mime.startswith("video/"):
        return "video"
    if mime.startswith("audio/"):
        return "podcast"
    return "other"


def parse_html(text):
    if not text.strip():
        return None
    return lxml_html.document_fromstring(text)


def _schema_nodes(tree):
    nodes = []
    for script in tree.xpath("//script[@type='application/ld+json']"):
        try:
            data = json.loads(script.text_content())
        except json.JSONDecodeError:
            # 页面自带的结构化数据不合法时不作为证据
            continue
        stack = [data]
        while stack:
            item = stack.pop()
            if isinstance(item, list):
                stack.extend(item)
            elif isinstance(item, dict):
                nodes.append(item)
                stack.extend(value for key, value in item.items() if key in ("@graph", "mainEntity", "hasPart", "itemListElement"))
    return nodes


def _schema_types(node):
    value = node.get("@type")
    values = value if isinstance(value, list) else [value]
    return {str(item).lower() for item in values if item}


def _meta(tree, *names):
    for name in names:
        values = tree.xpath(f"//meta[@property='{name}' or @name='{name}']/@content")
        if values:
            return values[0].strip().lower()
    return ""


def page_type(tree, body_text):
    """HTML 页面的内容类型及依据。"""
    evidence = []
    types = set()
    for node in _schema_nodes(tree):
        types |= _schema_types(node)
    og_type = _meta(tree, "og:type")
    if types & LISTING_SCHEMA_TYPES or og_type in ("product", "product.item"):
        evidence.append("schema_or_og:" + ",".join(sorted(types & LISTING_SCHEMA_TYPES) or [og_type]))
        return "listing", evidence
    if og_type.startswith("video"):
        return "video", ["og:type:" + og_type]
    if og_type.startswith("music") or "podcastepisode" in types:
        return "podcast", ["og_or_schema:podcast"]
    if types & ARTICLE_SCHEMA_TYPES or og_type == "article":
        evidence.append("schema_or_og:" + ",".join(sorted(types & ARTICLE_SCHEMA_TYPES) or [og_type]))
        return "article", evidence
    if body_text.strip():
        return "article", ["extracted_body"]
    return "unknown", []


def restrictions_from_status(status):
    """HTTP 状态码直接表达的限制或技术原因。"""
    if status == 401:
        return [{"kind": "login", "confidence": "confirmed", "evidence": "http_status:401"}], None
    if status == 402:
        return [{"kind": "paywall", "confidence": "confirmed", "evidence": "http_status:402"}], None
    if status == 403:
        return [{"kind": "permission_denied", "confidence": "confirmed", "evidence": "http_status:403"}], None
    if status == 451:
        return [{"kind": "region_blocked", "confidence": "confirmed", "evidence": "http_status:451"}], None
    if status == 429:
        return [], "rate_limited"
    if status in (404, 410):
        return [], "not_found"
    if status >= 500:
        return [], "server_error"
    if status >= 400:
        return [], "http_error"
    return [], None


def restrictions_from_html(tree, body_text, final_url):
    """根据页面结构识别限制。只看结构化标记、表单和页面标题，不看正文中的关键词。"""
    found = []
    title = (tree.findtext(".//title") or "").strip().lower()
    for selector in CAPTCHA_SELECTORS:
        if tree.xpath(selector):
            found.append({"kind": "captcha", "confidence": "confirmed", "evidence": "captcha_element"})
            break
    if not any(item["kind"] == "captcha" for item in found) and title in CAPTCHA_TITLES:
        found.append({"kind": "captcha", "confidence": "suspected", "evidence": "page_title:" + title})

    for node in _schema_nodes(tree):
        free = node.get("isAccessibleForFree")
        if free is False or str(free).lower() == "false":
            found.append({"kind": "paywall", "confidence": "confirmed", "evidence": "schema:isAccessibleForFree=false"})
            break
    if not any(item["kind"] == "paywall" for item in found):
        tier = _meta(tree, "article:content_tier")
        if tier in ("locked", "metered"):
            found.append({"kind": "paywall", "confidence": "confirmed", "evidence": "meta:article:content_tier=" + tier})
        elif tree.xpath(PAYWALL_CLASS_SELECTOR):
            found.append({"kind": "paywall", "confidence": "suspected", "evidence": "paywall_element"})

    short = len(body_text.strip()) < SHORT_BODY_CHARS
    if short and tree.xpath("//input[@type='password']"):
        found.append({"kind": "login", "confidence": "confirmed", "evidence": "password_form_with_short_body"})
    elif LOGIN_PATH.search(urlsplit(final_url).path):
        found.append({"kind": "login", "confidence": "suspected", "evidence": "redirected_to_login_path"})
    return found


def server_error_page(tree):
    """PHP 致命错误的固定输出结构：<b>Fatal error</b>: ... 。脚本已在此处终止，页面不含完整内容；只有 Warning 时不判定。"""
    for node in tree.xpath("//b"):
        label = (node.text or "").strip()
        if label in PHP_FATAL_LABELS and (node.tail or "").lstrip().startswith(":"):
            return "php_" + label.lower().replace(" ", "_")
    return None


def js_shell(tree, body_text):
    """抽取文本很少且页面只有前端框架挂载点或 noscript 提示时，判定需要 JS 渲染。"""
    if len(body_text.strip()) >= SHORT_BODY_CHARS:
        return None
    for node in tree.xpath(SHELL_CONTAINERS):
        if not node.text_content().strip():
            return "empty_app_container:" + (node.get("id") or "")
    if tree.xpath("//noscript") and len(tree.xpath("//script")) >= 3:
        return "noscript_with_scripts"
    return None
