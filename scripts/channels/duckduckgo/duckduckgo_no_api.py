import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from duckduckgo_search import DuckDuckGoSearch


class DuckDuckGoHtmlSearchNoAPI(DuckDuckGoSearch):
    ENGINE_NAME = 'duckduckgo'
    ENGINE_DISPLAY_NAME = 'DuckDuckGo'


def search_duckduckgo_html(query, max_results=None, proxy=None, **kwargs):
    return DuckDuckGoHtmlSearchNoAPI(proxy).search(query, max_results=max_results, **kwargs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DuckDuckGo 网页搜索')
    parser.add_argument('query')
    parser.add_argument('-m', '--max-results', type=int)
    parser.add_argument('--page', type=int, default=1)
    parser.add_argument('--timeout', type=float, default=20)
    parser.add_argument('--proxy')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    items = search_duckduckgo_html(args.query, args.max_results, args.proxy, page=args.page, timeout=args.timeout)
    print(json.dumps({'results': items}, ensure_ascii=False, indent=2))
