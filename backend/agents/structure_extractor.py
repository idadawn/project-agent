# backend/agents/structure_extractor.py
from typing import Dict, Any, List, Tuple
import re, os, pathlib, datetime

try:
    from .base import BaseAgent
except Exception:
    class BaseAgent:
        name = "base"
        def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
            return state

CANONICAL_SECTIONS = [
    "投标函","法定代表人身份证明","授权委托书","投标保证金",
    "投标报价表","分项报价表","企业资料","方案详细说明及施工组织设计",
    "资格审查资料","商务和技术偏差表","其他材料"
]

class StructureExtractor(BaseAgent):
    name = "structure_extractor"

    def __init__(self):
        super().__init__("structure_extractor")

    def get_system_prompt(self) -> str:
        return "你是投标文件结构抽取专家，从招标文件中抽取投标文件格式要求，生成标准投标文件骨架。"

    def _find_bid_format_block(self, text: str) -> Tuple[int,int]:
        start_pat = r"^#{1,6}\s*第\s*[五5V]\s*章.*?(投标文件格式|投标文件|投标文件格式[（(]样式[）)])"
        end_pat = r"^#{1,6}\s*第\s*[六6VI]\s*章|^#{1,6}\s*评标"
        s = re.search(start_pat, text, re.M)
        if not s:
            return (0, 0)
        e = re.search(end_pat, text[s.end():], re.M)
        if e:
            return (s.start(), s.end()+e.start())
        return (s.start(), len(text))

    def _extract_sections(self, block: str) -> List[str]:
        lines = block.splitlines()
        items: List[str] = []
        bullet = re.compile(r"^\s*([0-9０-９一二三四五六七八九十]+[.)、]|[-*•])\s*(.+?)\s*$")
        for ln in lines:
            m = bullet.match(ln)
            if m:
                item = re.sub(r"（.*?）|\(.*?\)", "", m.group(2)).strip()
                item = re.sub(r"\s+", "", item)
                if 2 <= len(item) <= 30:
                    items.append(item)

        norm = []
        for x in items:
            if "方案" in x and "施工" in x:
                norm.append("方案详细说明及施工组织设计")
            elif "偏差" in x:
                norm.append("商务和技术偏差表")
            else:
                norm.append(x)

        dedup: List[str] = []
        for x in norm:
            if x not in dedup:
                dedup.append(x)

        return dedup or CANONICAL_SECTIONS

    @staticmethod
    def _num(i:int)->str:
        CN="零一二三四五六七八九十"
        return CN[i] if 0<=i<len(CN) else str(i)

    def _render_skeleton(self, sections: List[str]) -> str:
        today = datetime.date.today().strftime("%Y-%m-%d")
        toc = "\n".join(f"{i+1}. {sec}" for i,sec in enumerate(sections))
        bodies = []
        for idx, sec in enumerate(sections, 1):
            bodies.append(f"## {self._num(idx)}、{sec}\n> [占位]\n")
        return f"""---
title: 投标文件（骨架）
generated_at: {today}
---

# 封面（模板）
- 项目名称：{{PROJECT_NAME}}
- 招标编号：{{TENDER_NO}}
- 投标人：{{BIDDER_NAME}}（盖章）
- 日期：{{YYYY}}年{{MM}}月{{DD}}日
- 正/副本：正本1份，副本4份

# 目 录
{toc}

---

{''.join(bodies)}

### 装订与份数提示
- 正本/副本分别装订成册并编目录；避免可拆装订。
"""

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # ✅ 统一用传入的 tender_path，不要再拼 uploads/
        tender_path = self._get_tender_path(state)
        wiki_dir = state.get("wiki_dir", "wiki")
        pathlib.Path(wiki_dir).mkdir(parents=True, exist_ok=True)

        with open(tender_path, "r", encoding="utf-8") as f:
            text = f.read()
        s, e = self._find_bid_format_block(text)
        sections = self._extract_sections(text[s:e]) if (s or e) else CANONICAL_SECTIONS
        content = self._render_skeleton(sections)

        out_path = os.path.join(wiki_dir, "投标文件_骨架.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

        state["outline_path"] = out_path
        state["outline_sections"] = sections
        return state
    
    def _get_tender_path(self, state: Dict[str, Any]) -> str:
        """统一解析招标文件路径"""
        from pathlib import Path
        
        # 1) 优先：传入的 tender_path
        p = state.get("tender_path")
        if p and Path(p).exists():
            return str(Path(p).resolve())
        
        # 2) 次优：从 meta 中获取
        meta = state.get("meta", {})
        p = meta.get("tender_path")
        if p and Path(p).exists():
            return str(Path(p).resolve())
        
        # 3) 次优：兼容路径
        p = meta.get("legacy_tender_path")
        if p and Path(p).exists():
            return str(Path(p).resolve())
        
        # 4) 占底：常见目录候选
        for candidate in [
            Path("uploads") / "招标文件.md",
            Path("/root/project/git/project-agent/uploads") / "招标文件.md",
            Path("wiki") / "招标文件.md",
            Path("/root/project/git/project-agent/wiki") / "招标文件.md",
        ]:
            if candidate.exists():
                return str(candidate.resolve())
        
        raise FileNotFoundError("未找到招标文件：tender_path/meta/legacy/candidates 均不存在")
