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

def _normalize(s: str) -> str:
    """宽松规范化：统一全/半角标点与空白，便于匹配。"""
    return (
        s.replace("：", ":")
         .replace("（", "(")
         .replace(")", ")")
         .replace("．", ".")
         .replace("、", ".")
         .replace("\ufeff", "")
         .replace("\u200b", "")
    ).strip()

def _strip_num_prefix(s: str) -> str:
    """移除条目前缀序号，如“一、/（一）/1.” 等。"""
    return re.sub(r"^\s*[（(]?[一二三四五六七八九十\d]+[)）]?[\.、:：]?\s*", "", s)


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


def remove_all_chapter_headings(block: str) -> str:
    """移除块内所有形如“# 第X章 ...”的 Markdown 标题行，避免残留目录/分章名。"""
    text = _norm(block)
    # 仅删除明确的章级标题（第X章），不影响 ##/### 内的小节标题
    pat = re.compile(r"(?m)^\s*#{1,6}\s*第\s*(?:[一二三四五六七八九十百千\d]+)\s*章.*$\n?")
    return pat.sub("", text).lstrip("\n")


def build_toc_item_list(md: str) -> List[str]:
    """从正文内的“目 录”区域提取条目列表（不含“目 录”本身）。"""
    lines = _norm(md).split("\n")
    # 寻找“目 录/目录”标题行（忽略空格差异）
    start = None
    for i, ln in enumerate(lines):
        key = _normalize(ln).replace(" ", "")
        if key in ("目录", "目录", "目录", "目录"):  # 兼容“目 录”与“目录”
            start = i
            break
    if start is None:
        return []

    items: List[str] = []
    item_pat = re.compile(r"^[(（]?[一二三四五六七八九十\d]+[)）]?[、.．:：]\s*.+")
    for j in range(start + 1, len(lines)):
        t = lines[j].strip()
        if not t:
            if items:
                break
            else:
                continue
        if item_pat.match(t):
            items.append(t)
        else:
            if items:
                break
    return items


def ensure_headings_for_toc(md: str, toc_items: List[str]) -> str:
    """
    为每个目录条目在正文中自动补充一个二级标题（## ...）。
    - 若能在正文定位到该条目关键词，则在其所在段落前插入标题
    - 若定位失败，则将标题插入到“目 录”之后的第一处合适位置（最小改造）
    """
    body = _norm(md)

    # 目录锚点（“目 录/目录”）位置，用于回退插入
    def _find_catalog_insert_pos(text: str) -> int:
        for key in ("目 录", "目录", "目录", "目录"):
            idx = text.find(key)
            if idx != -1:
                # 放在该行之后一行
                nl = text.find("\n", idx)
                return len(text) if nl == -1 else nl + 1
        return 0

    for item in toc_items:
        core = _strip_num_prefix(_normalize(item))
        # 已存在对应二级标题？
        pat_heading = re.compile(rf"(?m)^##\s*.*{re.escape(core)}.*$")
        if pat_heading.search(body):
            continue

        # 选择性锚点集合
        anchors = [
            core,
            core.replace("（", "(").replace("）", ")"),
            core.replace(" ", ""),
        ]
        pos = -1
        for a in anchors:
            m = re.search(re.escape(a), body)
            if m:
                pos = m.start()
                break

        heading = f"\n## {item}\n"
        if pos == -1:
            # 回退：插在目录之后第一行
            insert_at = _find_catalog_insert_pos(body)
            body = body[:insert_at] + heading + body[insert_at:]
        else:
            # 在该锚点前，回溯至段落起始（空行后）
            start_par = body.rfind("\n\n", 0, pos)
            insert_at = 0 if start_par == -1 else start_par + 2
            body = body[:insert_at] + heading + body[insert_at:]

    return body


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
    # 进一步清理所有可能残留的“第X章 ...”行
    section = remove_all_chapter_headings(section)
    # 基于“目 录”条目自动补二级标题，保证目录与正文可对齐
    toc_items = build_toc_item_list(section)
    if toc_items:
        section = ensure_headings_for_toc(section, toc_items)
    toc = outline(section, 2, 6)   # 统计二级及以下标题
    return section, toc


