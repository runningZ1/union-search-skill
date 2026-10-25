import base64
import re
from difflib import SequenceMatcher
from html import unescape
from urllib.parse import parse_qsl, unquote, urlsplit, urlunsplit

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


def _query_value(parsed, key):
    for part in parsed.query.split('&'):
        name, separator, value = part.partition('=')
        if separator and name.lstrip('!').lower() == key:
            return unquote(value)
    return ''


def _target_url(parsed):
    host = parsed.netloc.lower()
    if host.endswith('search.yahoo.com'):
        target = _query_value(parsed, 'ru')
        if not target:
            match = re.search(r'/RU=(.+?)/RK=', parsed.path)
            target = unquote(match.group(1)) if match else ''
        return target
    if host.endswith('bing.com'):
        token = re.sub(r'[^A-Za-z0-9+/]', '', _query_value(parsed, 'u'))
        if not token:
            return ''
        # Bing 跳转参数使用去掉末尾填充的 base64。
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
        parsed = urlsplit(target)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('搜索结果必须包含绝对 HTTP 或 HTTPS 地址')
    ignored = {'gclid', 'fbclid', 'msclkid', 'spm', 'spm_id_from', 'pvid', 'scene', 'wfr', 'for'}
    # 保持签名地址和服务生成参数的原始编码，仅删除已知跟踪字段。
    parts = []
    for part in parsed.query.split('&'):
        if not part:
            continue
        key = parse_qsl(part, keep_blank_values=True)[0][0].lower()
        if not key.startswith('utm_') and key not in ignored:
            parts.append(part)
    hostname = parsed.hostname.lower()
    if hostname.startswith('www.'):
        hostname = hostname[4:]
    port = f':{parsed.port}' if parsed.port else ''
    path = parsed.path.rstrip('/') or '/'
    return urlunsplit((parsed.scheme.lower(), hostname + port, path, '&'.join(parts), ''))


def _first_text(item, keys):
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ''


def normalize_item(item, platform, rank):
    url = _first_text(item, ('html_url', 'link', 'href', 'permalink', 'source_url', 'Url', 'url'))
    title = clean_text(_first_text(item, ('title', 'name', 'Title', 'full_name')))
    if not title:
        raise ValueError(f'{platform} 返回空标题')
    url = canonical_url(url)
    normalized = {
        'title': title,
        'url': url,
        'content': clean_text(_first_text(item, ('content', 'body', 'description', 'snippet', 'summary', 'Snippet'))),
        'published': _first_text(item, ('published', 'publishedDate', 'published_at', 'publish_date', 'date')) or None,
        'thumbnail': item.get('thumbnail') or None,
        'sources': item.get('sources') or [{'platform': platform, 'engine': item.get('engine') or platform, 'rank': rank}],
    }
    if item.get('link_type') == 'redirect':
        normalized['sources'][0]['link_type'] = 'redirect'
    return normalized


def comparable_title(value):
    return re.sub(r'[\W_]+', '', value.casefold(), flags=re.UNICODE)


def _absorb(existing, item):
    for source in item['sources']:
        if source not in existing['sources']:
            existing['sources'].append(source)
    if len(item['content']) > len(existing['content']):
        existing['content'] = item['content']
        existing['title'] = item['title']
    if not existing['published'] and item['published']:
        existing['published'] = item['published']
    if not existing['thumbnail'] and item['thumbnail']:
        existing['thumbnail'] = item['thumbnail']


def merge_items(items):
    output = []
    by_url = {}
    by_title = {}
    removed = 0
    for item in items:
        url_key = item['url']
        title_key = comparable_title(item['title'])
        existing = by_url.get(url_key) or by_title.get(title_key)
        if existing is None and title_key:
            for candidate in output:
                if SequenceMatcher(None, title_key, comparable_title(candidate['title'])).ratio() >= 0.9:
                    existing = candidate
                    break
        if existing is not None:
            _absorb(existing, item)
            by_url[url_key] = existing
            if title_key:
                by_title[title_key] = existing
            removed += 1
            continue
        row = {**item, 'sources': list(item['sources'])}
        output.append(row)
        by_url[url_key] = row
        if title_key:
            by_title[title_key] = row
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
    elif 'timed out' in lowered or 'timeout' in lowered or 'deadline' in lowered or '截止时间' in message or '超时' in message:
        code = 'TIMEOUT'
    elif 'ssl' in lowered or 'tls' in lowered:
        code = 'TLS_ERROR'
    elif '403' in message:
        code = 'ACCESS_DENIED'
    else:
        code = 'PLATFORM_ERROR'
    return {'code': code, 'message': message.strip().splitlines()[-1], 'retryable': code in ('TIMEOUT', 'TLS_ERROR')}
