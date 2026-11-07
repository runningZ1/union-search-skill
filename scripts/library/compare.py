import difflib
import hashlib
import os
import re
import unicodedata

_BLANK_RUN = re.compile(r"\n{3,}")
MAX_CHANGE_SAMPLES = 20
MAX_SAMPLE_CHARS = 300


def normalize_body(text):
    """只去除无意义的空白差异：统一换行、去掉行尾空格、压缩连续空行。不排序、不删段落，数字和表格保持原样。"""
    text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    lines = [line.rstrip() for line in text.split("\n")]
    return _BLANK_RUN.sub("\n\n", "\n".join(lines)).strip() + "\n"


def body_hash(normalized):
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def diff_stats(old, new):
    """逐行比较的增删改统计；相似度只用于诊断，是否覆盖由哈希决定。"""
    old_lines = old.split("\n")
    new_lines = new.split("\n")
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    added = removed = replaced = 0
    changes = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "insert":
            added += j2 - j1
        elif tag == "delete":
            removed += i2 - i1
        else:
            replaced += max(i2 - i1, j2 - j1)
        if len(changes) < MAX_CHANGE_SAMPLES:
            # 只记录变化处附近的片段，便于核对数字等修改；不保存旧全文
            old_part = "\n".join(old_lines[i1:i2])
            new_part = "\n".join(new_lines[j1:j2])
            start = max(0, len(os.path.commonprefix([old_part, new_part])) - 60)
            changes.append({"kind": tag, "offset": start, "old": old_part[start:start + MAX_SAMPLE_CHARS],
                            "new": new_part[start:start + MAX_SAMPLE_CHARS]})
    return {
        "added_lines": added,
        "removed_lines": removed,
        "replaced_lines": replaced,
        "old_chars": len(old),
        "new_chars": len(new),
        "changes": changes,
    }, round(matcher.ratio(), 6)
