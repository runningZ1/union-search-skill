from html import unescape
from urllib.parse import parse_qsl, urlsplit, urlunsplit

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


def canonical_url(value):
    parsed = urlsplit(value.strip())
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('搜索结果必须包含绝对 HTTP 或 HTTPS 地址')
    ignored = {'gclid', 'fbclid', 'msclkid'}
    # 保持签名地址和服务生成参数的原始编码，仅删除已知跟踪字段。
    parts = []
    for part in parsed.query.split('&'):
        if not part:
            continue
        key = parse_qsl(part, keep_blank_values=True)[0][0].lower()
        if not key.startswith('utm_') and key not in ignored:
            parts.append(part)
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or '/', '&'.join(parts), ''))


def normalize_item(item, platform, rank):
    url = next((item[key] for key in ('url', 'href', 'link', 'permalink', 'source_url') if item.get(key)), '')
    title = clean_text(item.get('title') or item.get('name') or '')
    if not title:
        raise ValueError(f'{platform} 返回空标题')
    url = canonical_url(url)
    normalized = {
        'title': title,
        'url': url,
        'content': clean_text(item.get('content') or item.get('body') or item.get('description') or item.get('snippet') or ''),
        'published': item.get('published') or item.get('publishedDate') or item.get('date') or None,
        'thumbnail': item.get('thumbnail') or None,
        'sources': item.get('sources') or [{'platform': platform, 'engine': item.get('engine') or platform, 'rank': rank}],
    }
    if item.get('link_type') == 'redirect':
        normalized['sources'][0]['link_type'] = 'redirect'
    return normalized


def merge_items(items, deduplicate):
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
            if len(item['content']) > len(existing['content']):
                existing['content'] = item['content']
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
    elif 'timed out' in lowered or 'timeout' in lowered or 'deadline' in lowered or '截止时间' in message or '超时' in message:
        code = 'TIMEOUT'
    elif 'ssl' in lowered or 'tls' in lowered:
        code = 'TLS_ERROR'
    elif '403' in message:
        code = 'ACCESS_DENIED'
    else:
        code = 'PLATFORM_ERROR'
    return {'code': code, 'message': message.strip().splitlines()[-1], 'retryable': code in ('TIMEOUT', 'TLS_ERROR')}
