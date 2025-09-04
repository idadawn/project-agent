# -*- coding: utf-8 -*-
"""
从整份 Markdown 中定位“最后一章”或匹配“投标文件格式”（含同义词）的章标题（必须是 # 开头），
截取该章至文末（或下一章标题前），并在去掉章标题行后，生成该章内的目录树（##/### 等小节）。

关键规则：
- 只认章标题：必须是 ^#{1,6}\s*第X章 开头；忽略目录链接与正文引用。
- 忽略章号：只要标题文本出现“投标文件格式/模板/范本/样本/投标格式”即可。
- “最后一章”优先：若 user_hint 含“最后/last”，或未命中关键词，则取文中最后一个章标题。
- 兼容全/半角与数字：支持 ：/: 以及 第五章/第5章。
"""

from typing import Optional, Tuple, List
import re


CHAPTER_SYNS_DEFAULT = [
    "投标文件格式",
    "投标文件模板",
    "投标格式",
    "投标文件范本",
    "投标文件样本",
]


def _norm(md: str) -> str:
    return md.replace("\r\n", "\n").replace("\r", "\n")


def find_chapter_span(md: str, user_hint: Optional[str] = None) -> Optional[Tuple[int, int]]:
    """
    返回 (start_idx, end_idx)，用于截取该章到下一章（含起始章标题行）。
    若为最后一章，则 end_idx 为 len(md)。
    仅匹配以 # 开头的章标题，避免目录/引用误命中。
    """
    text = _norm(md)
    syns = CHAPTER_SYNS_DEFAULT.copy()
    if user_hint:
        syns.insert(0, user_hint.strip())
    syn_group = "|".join(map(re.escape, syns))

    # 1) 严格：以#开头 + 第X章 + 同义词
    pat_strict = re.compile(
        rf"(?m)^\s*#{{1,6}}\s*第\s*(?:[一二三四五六七八九十百千\d]+)\s*章\s*[:：]?\s*(?:{syn_group})\s*$"
    )
    strict_matches = list(pat_strict.finditer(text))
    m = strict_matches[-1] if strict_matches else None

    # 2) “最后/last” 或未命中关键词 → 取最后一个章标题
    if (user_hint and ("最后" in user_hint or "last" in user_hint.lower())) or not m:
        pat_last = re.compile(r"(?m)^\s*#{1,6}\s*第\s*(?:[一二三四五六七八九十百千\d]+)\s*章.*$")
        last = None
        for mm in pat_last.finditer(text):
            last = mm
        m = m or last

    if not m:
        return None

    start = m.start()

    # 找下一章标题作为 end（如果存在）
    pat_next = re.compile(r"(?m)^\s*#{1,6}\s*第\s*(?:[一二三四五六七八九十百千\d]+)\s*章.*$")
    next_m = None
    for mm in pat_next.finditer(text, m.end()):
        next_m = mm
        break
    end = next_m.start() if next_m else len(text)
    return (start, end)


def strip_first_heading(block: str) -> str:
    """去掉首行章标题（如果有）"""
    lines = _norm(block).split("\n")
    if lines and re.match(r"^\s*#{1,6}\s*第\s*(?:[一二三四五六七八九十百千\d]+)\s*章", lines[0]):
        return "\n".join(lines[1:]).lstrip("\n")
    return "\n".join(lines)


def outline(block: str, min_level: int = 2, max_level: int = 6) -> List[str]:
    """
    生成目录树，返回标题行（去掉#的文本），仅统计 ## 到 ######。
    例如返回：["## 目 录", "### 一、投标函", ...]
    """
    text = _norm(block)
    pat = re.compile(rf"(?m)^\s*#{{{min_level},{max_level}}}\s+(.+?)\s*$")
    items: List[str] = []
    for m in pat.finditer(text):
        full_line = m.group(0).strip()
        items.append(full_line)
    return items


def extract_bid_format_section(md: str, user_hint: Optional[str] = None, drop_heading: bool = True):
    span = find_chapter_span(md, user_hint=user_hint)
    if not span:
        return None, []
    start, end = span
    section = _norm(md)[start:end]
    if drop_heading:
        section = strip_first_heading(section)
    toc = outline(section, 2, 6)   # 统计二级及以下标题
    return section, toc


