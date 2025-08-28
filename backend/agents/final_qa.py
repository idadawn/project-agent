from typing import Dict, Any
import os, json
from .base import BaseAgent

class FinalQA(BaseAgent):
    def __init__(self):
        super().__init__("final_qa")
    
    def get_system_prompt(self) -> str:
        return "你是终检专家。对照招标文件组成与评标办法，输出QA报告。"

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        wiki_dir = state.get("wiki_dir", "wiki")
        final_path = state.get("final_bid_path") or state.get("draft_path")
        spec_path = state.get("spec_path")
        qa_path = os.path.join(wiki_dir, "qa_report.json")

        final_text = self._safe_read(final_path)
        spec_text = self._safe_read(spec_path)

        result = {
            "composition_complete": all(k in final_text for k in [
                "投标函","法定代表人身份证明","授权委托书","投标保证金",
                "投标报价表","分项报价表","企业资料","方案详细说明及施工组织设计",
                "资格审查资料","商务和技术偏差表","其他材料"
            ]),
            "scoring_covered": all(k in final_text for k in [
                "技术方案（25分}", "施工方法及主要技术措施（25分"
            ]) or ("技术方案" in final_text and "施工方法" in final_text),
            "schedule_constraints": ("180天" in spec_text and "150天" in spec_text and ("180" in final_text or "150" in final_text)),
            "safety_env_constraints": all(k in spec_text for k in ["安全","环保"]) and ("安全" in final_text and "环保" in final_text)
        }

        with open(qa_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        state["qa_report_path"] = qa_path
        return state

    def _safe_read(self, path: str) -> str:
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""
