# backend/agents/spec_extractor.py
from typing import Dict, Any, Tuple
import re, os, pathlib, datetime

try:
    from .base import BaseAgent
except Exception:
    class BaseAgent:
        name = "base"
        def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
            return state

class SpecExtractor(BaseAgent):
    name = "spec_extractor"

    START_PATS = [
        r"^#{1,6}\s*第\s*[四4IV]\s*章.*?(技术规格书|技术要求)",
    ]
    END_PATS = [
        r"^#{1,6}\s*第\s*[五5V]\s*章", r"^#{1,6}\s*投标文件格式"
    ]

    def _slice(self, text:str)->Tuple[int,int]:
        s = None
        for p in self.START_PATS:
            s = re.search(p, text, re.M)
            if s: break
        if not s:
            return (0,0)
        e = None
        for p in self.END_PATS:
            e = re.search(p, text[s.end():], re.M)
            if e: break
        if e:
            return (s.start(), s.end()+e.start())
        return (s.start(), len(text))

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        tender_path = state.get("tender_path") or "uploads/招标文件.md"
        wiki_dir = state.get("wiki_dir", "wiki")
        pathlib.Path(wiki_dir).mkdir(parents=True, exist_ok=True)

        with open(tender_path, "r", encoding="utf-8") as f:
            text = f.read()
        s,e = self._slice(text)
        payload = text[s:e].strip() if (s or e) else (
            "# 第四章 技术规格书（未在文中定位，使用提纲占位）\n\n"
            "- 交钥匙范围\n- 技术参数与标准\n- 资料交付\n- 质量与验收\n- 安全与环保\n"
        )
        head = f"""---
title: 技术规格书（提取）
generated_at: {datetime.date.today().strftime("%Y-%m-%d")}
note: 由 SpecExtractor 自动抽取（从“第四章 技术规格书/技术要求”至“第五章/投标文件格式”前）
---

"""
        out = os.path.join(wiki_dir, "技术规格书_提取.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(head+payload+"\n")
        state["spec_path"] = out
        state["spec_extracted"] = bool(s or e)
        return state
