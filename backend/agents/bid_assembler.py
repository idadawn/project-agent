# backend/agents/bid_assembler.py
from typing import Dict, Any
import os, pathlib, datetime

try:
    from .base import BaseAgent
except Exception:
    class BaseAgent:
        name = "base"
        def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
            return state

class BidAssembler(BaseAgent):
    name = "bid_assembler"

    def __init__(self):
        super().__init__("bid_assembler")

    def get_system_prompt(self) -> str:
        return "你是投标文件拼装专家，将骨架、方案提纲和技术规格书进行智能拼装生成投标文件草案。"

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        wiki_dir = state.get("wiki_dir", "wiki")
        outline_path = state.get("outline_path")
        plan_path = state.get("plan_path")
        spec_path = state.get("spec_path")

        outline = self._safe_read(outline_path)
        plan = self._safe_read(plan_path)
        spec = self._safe_read(spec_path)

        assembled = self._merge(outline, plan, spec)
        out = os.path.join(wiki_dir, "投标文件_草案.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(assembled)
        state["draft_path"] = out
        return state

    @staticmethod
    def _safe_read(path:str)->str:
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def _merge(self, outline:str, plan:str, spec:str)->str:
        today = datetime.date.today().strftime("%Y-%m-%d")
        return f"""---
title: 投标文件（草案）
generated_at: {today}
note: 自动拼装：骨架 + 方案提纲（其余章节留占位）
---

{outline}

---

## 八、方案详细说明及施工组织设计（合并）
> 以下为自动合并的《方案（提纲）》内容：

{plan}

---

### 附：技术规格书（提取节选）
> 供方案引用与一致性检查

{spec[:20000]}
"""
