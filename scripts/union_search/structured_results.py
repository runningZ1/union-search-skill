import base64
import re
from html import unescape
from urllib.parse import unquote, urlsplit, urlunsplit

from lxml import html


def clean_text(value):
    if value is None:
        return ''
    if not isinstance(value, str):
        raise TypeError('搜索文本字段必须为字符串')
    if '<' in value and '>' in value:
        tree = html.fragment_fromstring(value, create_parent='div')
        for node in tree.xpath('.//script | .//style'):
            node.drop_tree()
        value = tree.text_content()
    return ' '.join(unescape(value).split())


def _first_text(item, keys):
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ''


def _query_value(parsed, key):
    for part in parsed.query.split('&'):
        name, separator, value = part.partition('=')
        if separator and name.lstrip('!').lower() == key:
            return unquote(value)
    return ''


def _target_url(parsed):
    """把搜索引擎跳转链接还原成目标页，便于同一页面跨渠道合并。"""
    host = parsed.netloc.lower()
    if host.endswith('search.yahoo.com') or host.endswith('r.search.yahoo.com'):
        target = _query_value(parsed, 'ru')
        if not target:
            match = re.search(r'/RU=(.+?)/RK=', parsed.path)
            target = unquote(match.group(1)) if match else ''
        return target
    if host.endswith('bing.com'):
        token = re.sub(r'[^A-Za-z0-9+/]', '', _query_value(parsed, 'u'))
        if not token:
            return ''
        payload = token[2:] if token.startswith('a1') else token
        padded = payload + '=' * ((4 - len(payload) % 4) % 4)
        try:
            return base64.b64decode(padded).decode('utf-8')
        except (ValueError, UnicodeDecodeError):
            return ''
    return ''


def canonical_url(value):
    parsed = urlsplit(value.strip())
    target = _target_url(parsed)
    if target:
        parsed = urlsplit(target.strip())
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('搜索结果必须包含绝对 HTTP 或 HTTPS 地址')
    ignored = {'gclid', 'fbclid', 'msclkid', 'spm', 'spm_id_from'}
    parts = []
    for part in parsed.query.split('&'):
        if not part:
            continue
        key = part.split('=', 1)[0].lstrip('!').lower()
        if not key.startswith('utm_') and key not in ignored:
            parts.append(part)
    hostname = parsed.hostname.lower()
    if hostname.startswith('www.'):
        hostname = hostname[4:]
    port = f':{parsed.port}' if parsed.port else ''
    path = parsed.path.rstrip('/') or '/'
    return urlunsplit((parsed.scheme.lower(), hostname + port, path, '&'.join(parts), ''))


def normalize_item(item, platform, rank):
    # html_url 是网页地址；GitHub 等接口的 url 常指向 API，不能优先使用。
    url = _first_text(item, ('html_url', 'link', 'href', 'permalink', 'source_url', 'Url', 'url'))
    title = clean_text(_first_text(item, ('title', 'name', 'Title', 'full_name')))
    if not title:
        raise ValueError(f'{platform} 返回空标题')
    url = canonical_url(url)
    published = None
    for key in ('published', 'publishedDate', 'published_at', 'publish_date', 'date'):
        value = item.get(key)
        if value:
            published = value
            break
    normalized = {
        'title': title,
        'url': url,
        'content': clean_text(_first_text(item, ('content', 'body', 'description', 'snippet', 'summary', 'Snippet'))),
        'published': published,
        'thumbnail': item.get('thumbnail') or None,
        'sources': item.get('sources') or [{'platform': platform, 'engine': item.get('engine') or platform, 'rank': rank}],
    }
    if item.get('link_type') == 'redirect':
        normalized['sources'][0]['link_type'] = 'redirect'
    return normalized


def merge_items(items, deduplicate=True):
    """按规范化后的页面地址合并。不同地址不因标题相近而合并。"""
    output = []
    by_url = {}
    removed = 0
    for item in items:
        key = item['url']
        if deduplicate and key in by_url:
            existing = by_url[key]
            for source in item['sources']:
                if source not in existing['sources']:
                    existing['sources'].append(source)
            if len(item.get('content') or '') > len(existing.get('content') or ''):
                existing['content'] = item['content']
            if not existing.get('published') and item.get('published'):
                existing['published'] = item['published']
            if not existing.get('thumbnail') and item.get('thumbnail'):
                existing['thumbnail'] = item['thumbnail']
            removed += 1
        else:
            row = {**item, 'sources': list(item['sources'])}
            output.append(row)
            by_url[key] = row
    for index, item in enumerate(output, 1):
        item['id'] = index
    return output, removed


def error_details(message):
    lowered = message.lower()
    if 'searchcooldownerror' in lowered or 'cooldownactiveerror' in lowered:
        code = 'COOLDOWN'
    elif '429' in message or 'too many requests' in lowered:
        code = 'RATE_LIMITED'
    elif 'captcha' in lowered or '验证码' in message or '验证页面' in message:
        code = 'CAPTCHA'
    elif any(phrase in lowered for phrase in ('timed out', 'time out', 'read timeout', 'connect timeout', 'timeout expired', 'deadline')) or '超时' in message or '截止时间' in message:
        code = 'TIMEOUT'
    elif 'ssl' in lowered or 'tls' in lowered:
        code = 'TLS_ERROR'
    elif '403' in message:
        code = 'ACCESS_DENIED'
    else:
        code = 'PLATFORM_ERROR'
    return {'code': code, 'message': message.strip().splitlines()[-1], 'retryable': code in ('TIMEOUT', 'TLS_ERROR')}
