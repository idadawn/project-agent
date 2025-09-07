# -*- coding: utf-8 -*-
"""
从整份 Markdown 中定位"最后一章"或匹配"投标文件格式"（含同义词）的章标题（必须是 # 开头），
截取该章至文末（或下一章标题前），并在去掉章标题行后，生成该章内的目录树（##/### 等小节）。

关键规则：
- 只认章标题：必须是 ^#{1,6}\s*第X章 开头；忽略目录链接与正文引用。
- 忽略章号：只要标题文本出现"投标文件格式/模板/范本/样本/投标格式"即可。
- "最后一章"优先：若 user_hint 含"最后/last"，或未命中关键词，则取文中最后一个章标题。
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

    # 2) "最后/last" 或未命中关键词 → 取最后一个章标题
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
    """移除块内所有形如"# 第X章 ..."的 Markdown 标题行，避免残留目录/分章名。"""
    text = _norm(block)
    # 仅删除明确的章级标题（第X章），不影响 ##/### 内的小节标题
    pat = re.compile(r"(?m)^\s*#{1,6}\s*第\s*(?:[一二三四五六七八九十百千\d]+)\s*章.*$\n?")
    return pat.sub("", text).lstrip("\n")


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
    # 进一步清理所有可能残留的"第X章 ..."行
    section = remove_all_chapter_headings(section)
    toc = outline(section, 2, 6)   # 统计二级及以下标题
    return section, toc


# =========================
# 通用：章节归一化 + 状态机（技术规格书专用）
# =========================

# 中文数字映射（简化覆盖：个、十、百 + 〇）
CN_NUM_MAP = {
    "零": 0, "〇": 0,
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9,
    "十": 10, "百": 100,
}


def cn2int(s: str) -> int:
    s = (s or "").strip()
    if not s:
        return 0
    # 阿拉伯数字
    if re.fullmatch(r"\d+", s):
        try:
            return int(s)
        except Exception:
            return 0
    # 百位（简单处理，不处理复杂千位）
    total = 0
    if "百" in s:
        parts = s.split("百")
        left = CN_NUM_MAP.get(parts[0], 1)
        total += left * 100
        s = parts[1] if len(parts) > 1 else ""
        if not s:
            return total
    # 十位
    if "十" in s:
        parts = s.split("十")
        left = CN_NUM_MAP.get(parts[0], 1)
        total += left * 10
        s = parts[1] if len(parts) > 1 else ""
        if s:
            total += CN_NUM_MAP.get(s, 0)
        return total
    # 个位
    return CN_NUM_MAP.get(s, 0)


# 标题匹配（强/弱/加粗兜底）
RE_STRONG = re.compile(
    r"^\s*#{0,6}\s*\*{0,2}第?\s*([一二三四五六七八九十百零〇0-9]+)\s*章[：:\.．、\s-]*([^\n#\r]*)\*{0,2}\s*$"
)
RE_WEAK = re.compile(
    r"^\s*#{0,6}\s*\*{0,2}([一二三四五六七八九十百零〇0-9]+)\s*章\s*([^\n#\r]*)\*{0,2}\s*$"
)
RE_BOLD = re.compile(r"^\s*\*{2}(.{0,50}章.{0,50})\*{2}\s*$")

TECH_KEYWORDS = (
    "技术规格书",
    "技术规范",
    "技术标准及规格",
    "技术标准",
    "技术条件",
)


def _is_toc_line(line: str) -> bool:
    # 常见目录/锚点：Word 导出锚点、Markdown 链接目录
    s = (line or "").strip()
    if not s:
        return False
    if "#_Toc" in s:
        return True
    is_md_link = s.startswith("**[") and "](" in s
    is_anchor_link = s.startswith("[") and "](#" in s
    if is_md_link or is_anchor_link:
        return True
    # 明显"目录"行，且带链接/页码点线时，更像 TOC
    if ("目录" in s) and (".." in s or ". ." in s or "](" in s):
        return True
    return False


def _detect_heading(line: str) -> Tuple[Optional[int], Optional[str]]:
    for pat in (RE_STRONG, RE_WEAK):
        m = pat.match(line)
        if m:
            num_raw = m.group(1)
            title = (m.group(2) or "").strip()
            # Clean up markdown formatting from title
            title = title.rstrip('*').strip()
            try:
                idx = cn2int(num_raw)
            except Exception:
                idx = None
            return idx, title
    mb = RE_BOLD.match(line)
    if mb:
        text = mb.group(1)
        m2 = re.search(r"第?\s*([一二三四五六七八九十百零〇0-9]+)\s*章", text)
        if m2:
            idx = cn2int(m2.group(1))
            title = text.split("章", 1)[-1].strip(" ：:．。.、-")
            return idx, title
    return None, None


def extract_tech_spec_section(md_text: str, include_heading: bool = True) -> Optional[str]:
    """
    从"第四章 技术规格书/技术规范/技术标准及规格/技术标准/技术条件"开始，
    抓取至"第五章"或"投标文件格式"章出现的上一行结束。兼容不同标题写法、中文/阿拉伯数字、目录过滤。
    返回包含起始章标题的文本（可通过 include_heading 控制）。未命中返回 None。
    """
    text = _norm(md_text)
    lines = text.split("\n")

    # 跳过前部目录区域：以首次出现"第一章/第1章/1 章"等非 TOC 行作为正文起点
    body_start = 0
    for i, ln in enumerate(lines[:200]):
        idx, _ = _detect_heading(ln)
        if idx == 1 and not _is_toc_line(ln):
            body_start = i
            break

    state = "OUTSIDE"
    buf: List[str] = []
    captured = False
    for ln in lines[body_start:]:
        idx, title = _detect_heading(ln)
        if idx is not None:
            if state == "OUTSIDE":
                if idx == 4 and (not title or any(k in title for k in TECH_KEYWORDS)):
                    state = "IN_TECH"
                    captured = True
                    if include_heading:
                        buf.append(ln)
                    continue
            elif state == "IN_TECH":
                # 遇到真正的下一章（第五章投标文件格式）时停止
                # 技术规格书内部的所有章节都应该继续
                should_stop = False
                
                # 检查是否是明确的下一章格式（第五章包含投标文件格式关键词）
                if ("第五章" in ln or "第5章" in ln) and title and any(k in title for k in ["投标文件格式", "投标格式", "投标模板"]):
                    should_stop = True
                # 或者遇到任何章节包含投标文件格式关键词（无论章节号）
                elif title and any(k in title for k in ["投标文件格式", "投标格式", "投标模板"]):
                    should_stop = True
                
                if should_stop:
                    break
                # 技规书内部的所有章节标题，继续纳入
                buf.append(ln)
                continue
        else:
            if state == "IN_TECH":
                buf.append(ln)

    if not captured:
        return None
    return "\n".join(buf).strip("\n")