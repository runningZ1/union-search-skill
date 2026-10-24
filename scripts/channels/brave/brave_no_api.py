import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brave.brave_search import BraveSearch, main


class BraveSearchNoAPI(BraveSearch):
    def search(self, query, max_results=None, timeout=20, **kwargs):
        return super().search(query, max_results=max_results, timeout=timeout, **kwargs)


def search_brave(query, max_results=None, proxy=None, **kwargs):
    return BraveSearchNoAPI(proxy=proxy).search(query, max_results=max_results, **kwargs)


if __name__ == '__main__':
    main()
