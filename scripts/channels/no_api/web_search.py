import math
import os
import time
from urllib.parse import urljoin, urlparse

from curl_cffi import requests
from lxml import html

from .request_state import CAPTCHA_COOLDOWN, CooldownActiveError, RequestState, retry_after_seconds


_STATE = RequestState()


class SearchBlockedError(RuntimeError):
    pass


class SearchCooldownError(SearchBlockedError):
    def __init__(self, error):
        self.host = error.host
        self.remaining = error.remaining
        self.reason = error.reason
        super().__init__(str(error))


class SearchDeadline:
    def __init__(self, timeout):
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('timeout 必须是大于零的有限数值')
        self.end = time.monotonic() + timeout

    def remaining(self):
        remaining = self.end - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('搜索请求超过截止时间')
        return remaining


def create_session(proxy=None):
    return requests.Session(impersonate='chrome', proxy=proxy or os.getenv('NO_API_KEY_PROXY'))


def block(response):
    host = urlparse(response.url).hostname
    _STATE.cooldown(host, CAPTCHA_COOLDOWN, 'captcha')
    origin_host = getattr(response, '_search_request_host', host)
    if origin_host != host:
        _STATE.cooldown(origin_host, CAPTCHA_COOLDOWN, 'captcha')
    raise SearchBlockedError(f'{host} 返回验证码页面，冷却 {CAPTCHA_COOLDOWN:.0f}s')


def _response_is_blocked(response):
    locations = (response.url, urljoin(response.url, response.headers.get('Location', '')))
    return response.headers.get('x-yandex-captcha') == 'captcha' or any(
        marker in urlparse(location).path.lower()
        for location in locations for marker in ('/captcha', '/showcaptcha', '/antispider')
    )


def _document_is_blocked(tree):
    if tree.xpath(
        '//form[@id="challenge-form" or contains(@action,"captcha")]'
        ' | //input[@name="captcha"] | //iframe[contains(@src,"captcha")]'
        ' | //script[contains(@src,"x5sec") or contains(.,"_____tmd_____/") or contains(.,"window._config_")]'
    ):
        return True
    heading = ' '.join(tree.xpath('//title//text()'))
    return any(marker in heading for marker in ('验证码', '用户验证', '安全验证', '访问异常'))


def request(session, method, url, timeout=20, **kwargs):
    deadline = SearchDeadline(timeout)
    host = urlparse(url).hostname
    try:
        _STATE.reserve(host, deadline.end)
    except CooldownActiveError as error:
        raise SearchCooldownError(error) from error
    response = session.request(method, url, timeout=deadline.remaining(), **kwargs)
    response._search_request_host = host
    if response.status_code == 429:
        duration = retry_after_seconds(response.headers.get('Retry-After'))
        _STATE.cooldown(host, duration, 'HTTP 429')
        final_host = urlparse(response.url).hostname
        if final_host != host:
            _STATE.cooldown(final_host, duration, 'HTTP 429')
        response.raise_for_status()
    if _response_is_blocked(response):
        block(response)
    response.raise_for_status()
    deadline.remaining()
    return response


def document(response):
    tree = html.fromstring(response.content, parser=html.HTMLParser(encoding=response.encoding or 'utf-8'), base_url=response.url)
    if _response_is_blocked(response) or _document_is_blocked(tree):
        block(response)
    return tree


def text(node):
    if isinstance(node, str):
        value = node
    elif isinstance(node, list):
        value = ' '.join(text(item) for item in node)
    else:
        value = node.text_content()
    return ' '.join(value.split())


def result(title, url, content, engine, **extra):
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise ValueError(f'{engine} 返回无效的网页地址')
    title = text(title)
    if not title:
        raise ValueError(f'{engine} 返回空标题')
    content = text(content)
    return {'title': title, 'url': url, 'content': content, 'href': url, 'body': content, 'engine': engine, **extra}


def validate_options(page, max_results, timelimit):
    if page < 1:
        raise ValueError('page 必须大于零')
    if max_results is not None and max_results < 0:
        raise ValueError('max_results 不能小于零')
    if timelimit is not None and timelimit not in ('d', 'w', 'm', 'y'):
        raise ValueError('timelimit 仅支持 d、w、m、y')
