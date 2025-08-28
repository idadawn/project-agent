from typing import Dict, Any, List
import os
from .base import BaseAgent

class DiffTableBuilder(BaseAgent):
    def __init__(self):
        super().__init__("diff_table_builder")
    
    def get_system_prompt(self) -> str:
        return "你是偏差比对分析专家，对比技术规格书与投标文本，生成商务和技术偏差表。"

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        wiki_dir = state.get("wiki_dir", "wiki")
        spec_path = state.get("spec_path")
        final_path = state.get("final_bid_path") or state.get("draft_path")
        out_path = os.path.join(wiki_dir, "偏差表.md")

        spec = self._safe_read(spec_path)
        bid = self._safe_read(final_path)

        table = self._build_diff(spec, bid)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(table)

        state["diff_table_path"] = out_path
        return state

    def _safe_read(self, path: str) -> str:
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def _build_diff(self, spec: str, bid: str) -> str:
        # 极简实现：按关键词检查是否响应，未发现差异则写“无”
        keywords: List[str] = ["交钥匙", "资料交付", "检验", "验收", "安全", "环保", "排放", "工期"]
        rows: List[str] = []
        for kw in keywords:
            in_spec = kw in spec
            in_bid = kw in bid
            if in_spec and not in_bid:
                rows.append(f"- 关键词：{kw} | 偏差：投标文本未明确响应 | 建议：补充对{kw}条款的承诺与指标")
        if not rows:
            return "# 商务和技术偏差表\n\n无\n"
        return "# 商务和技术偏差表\n\n" + "\n".join(rows) + "\n"
