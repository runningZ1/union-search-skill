"""Search presentation and local full-result retrieval."""

from copy import deepcopy
import json
from pathlib import Path
import uuid

from errors import CliUsageError


def write_full_result(envelope):
    """本次完整搜索信封写入 .work，供 read --from-file 读取；长期保存由资料库负责。"""
    archive_dir = Path.cwd() / '.work' / 'search-results' / uuid.uuid4().hex
    archive_dir.mkdir(parents=True, exist_ok=False)
    archive = archive_dir / 'full.json'
    envelope['meta']['full_result_file'] = str(archive)
    archive.write_text(json.dumps(envelope, ensure_ascii=False), encoding='utf-8')


def project_search(envelope, view, content_mode):
    """展示投影：渠道原始字段只入库不展示；content=none 只隐藏展示，不影响归档。"""
    result = deepcopy(envelope)
    data = result['data']
    if view == 'compact' and 'final_items' in data:
        data.pop('results', None)
        data.pop('download_candidates', None)
    collections = [data.get('final_items', []), data.get('items', [])]
    collections.extend(channel.get('items', []) for channel in data.get('results', {}).values())
    for rows in collections:
        for index, row in enumerate(rows, 1):
            row.setdefault('id', index)
            row.pop('raw', None)
            if content_mode == 'none':
                row.pop('content', None)
    result['meta'].update(view=view, content_mode=content_mode)
    return result


def read_results(source, ids):
    path = Path(source).resolve()
    envelope = json.loads(path.read_text(encoding='utf-8'))
    archive = envelope.get('meta', {}).get('full_result_file')
    if archive and Path(archive).resolve() != path:
        envelope = json.loads(Path(archive).read_text(encoding='utf-8'))
    data = envelope.get('data', {})
    rows = data.get('final_items', data.get('items', []))
    indexed = {row.get('id', index): row for index, row in enumerate(rows, 1)}
    missing = [identifier for identifier in ids if identifier not in indexed]
    if missing:
        raise CliUsageError(f'Unknown result IDs: {missing}')
    return {'query': envelope.get('query'), 'success': True,
            'data': {'items': [{**{key: value for key, value in indexed[identifier].items() if key != 'raw'}, 'id': identifier} for identifier in ids]},
            'meta': {'source_ok': envelope.get('ok'), 'source_file': str(path)}}
