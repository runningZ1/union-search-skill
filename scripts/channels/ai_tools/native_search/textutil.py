import re
from urllib.parse import urlparse

_ENTITIES = {"amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'", "nbsp": " "}


def decode_entities(value: str) -> str:
    value = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), value)
    value = re.sub(r"&#x([0-9a-f]+);", lambda m: chr(int(m.group(1), 16)), value, flags=re.I)

    def named(match: re.Match[str]) -> str:
        return _ENTITIES.get(match.group(1).lower(), match.group(0))

    return re.sub(r"&([a-z]+);", named, value, flags=re.I)


def strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", decode_entities(re.sub(r"<[^>]+>", " ", value))).strip()


def clip(value: str, max_chars: int) -> tuple[str, bool]:
    if len(value) <= max_chars:
        return value, False
    return value[:max_chars], True


def hostname_of(url: str) -> str:
    host = urlparse(url).hostname or ""
    return host.removeprefix("www.")


def dedupe_hits(hits: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for hit in hits:
        key = hit.get("url", "").split("#", 1)[0].rstrip("/")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(hit)
    return out
