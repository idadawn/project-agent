# backend/agents/sanity_checker.py
from typing import Dict, Any, List
import os, re, json

try:
    from .base import BaseAgent
except Exception:
    class BaseAgent:
        name = "base"
        def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
            return state

MANDATORY_HINTS = [
    "工期","里程碑","第三方检测","验收","环保","安全","资料交付","质量标准","偏差表"
]

class SanityChecker(BaseAgent):
    name = "sanity_checker"

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        draft_path = state.get("draft_path")
        wiki_dir = state.get("wiki_dir", "wiki")
        text = ""
        if draft_path and os.path.exists(draft_path):
            with open(draft_path, "r", encoding="utf-8") as f:
                text = f.read()

        sections = state.get("outline_sections", [])
        missing_sections = [s for s in ["方案详细说明及施工组织设计"] if not re.search(s, text)]
        missing_hints = [h for h in MANDATORY_HINTS if h not in text]

        report = {
            "sections_in_outline": sections,
            "missing_core_sections": missing_sections,
            "missing_keywords": missing_hints,
            "suggestion": "请在方案中明确工期/环保/安全/第三方检测/资料交付等硬性条款的指标与验收口径；若与规格书不一致，请在商务和技术偏差表中列出。"
        }
        out = os.path.join(wiki_dir, "sanity_report.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        state["sanity_report"] = report
        state["sanity_report_path"] = out
        return state
