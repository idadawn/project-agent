from typing import Dict, Any
import os, json, datetime
from .base import BaseAgent

class AssemblerCompliance(BaseAgent):
    def __init__(self):
        super().__init__("assembler_compliance")
    
    def get_system_prompt(self) -> str:
        return "你是投标装配与合规校验专家，负责将方案合入骨架并完成合规性检查。"

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        wiki_dir = state.get("wiki_dir", "wiki")
        outline_path = state.get("outline_path")
        plan_draft_path = state.get("plan_draft_path")
        final_path = os.path.join(wiki_dir, "投标文件.md")

        outline = self._safe_read(outline_path)
        plan = self._safe_read(plan_draft_path)

        merged = self._merge_into_section_eight(outline, plan)
        with open(final_path, "w", encoding="utf-8") as f:
            f.write(merged)

        # 合规性检查
        compliance = self._check_compliance(merged)
        comp_path = os.path.join(wiki_dir, "compliance_report.json")
        with open(comp_path, "w", encoding="utf-8") as f:
            json.dump(compliance, f, ensure_ascii=False, indent=2)

        state["final_bid_path"] = final_path
        state["compliance_report"] = compliance
        state["compliance_report_path"] = comp_path
        return state

    def _safe_read(self, path: str) -> str:
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def _merge_into_section_eight(self, outline: str, plan: str) -> str:
        # 简单规则：找到“方案详细说明及施工组织设计”小节，将其占位替换为方案内容
        if not outline:
            return plan or ""
        marker = "方案详细说明及施工组织设计"
        lines = outline.splitlines()
        out_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            out_lines.append(line)
            if marker in line:
                # 跳过紧随其后的占位行
                j = i + 1
                while j < len(lines) and lines[j].strip().startswith(">"):
                    j += 1
                out_lines.append("\n" + plan.strip() + "\n")
                i = j
                continue
            i += 1
        return "\n".join(out_lines)

    def _check_compliance(self, text: str) -> Dict[str, Any]:
        required_sections = [
            "投标函","法定代表人身份证明","授权委托书","投标保证金",
            "投标报价表","分项报价表","企业资料","方案详细说明及施工组织设计",
            "资格审查资料","商务和技术偏差表","其他材料"
        ]
        missing = [s for s in required_sections if s not in text]
        checks = {
            "has_toc": ("# 目 录" in text) or ("# 目录" in text),
            "has_binding_hint": ("装订" in text and "副本" in text),
            "sections_missing": missing,
            "timestamp": datetime.datetime.now().isoformat()
        }
        return checks
