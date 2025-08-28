from typing import Dict, Any, List
import os, re, json
from .base import BaseAgent

MANDATORY_HINTS = [
    "工期","里程碑","第三方检测","验收","环保","安全","资料交付","质量标准","偏差表"
]

class SanityChecker(BaseAgent):
    def __init__(self):
        super().__init__("sanity_checker")
    
    def get_system_prompt(self) -> str:
        return """你是一个投标文件完整性检查专家。负责检查投标文件是否包含所有必要的内容和格式要求。"""

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """同步执行方法，用于LangGraph工作流"""
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
        
        # 持久化报告
        out = os.path.join(wiki_dir, "sanity_report.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        state["sanity_report_path"] = out
        state["sanity_report"] = report
        return state

    async def execute_async(self, context: Any) -> Any:
        """保持原有的异步接口兼容性"""
        draft_path = context.get("draft_path")
        text = ""
        if draft_path and os.path.exists(draft_path):
            with open(draft_path, "r", encoding="utf-8") as f:
                text = f.read()

        sections = context.get("outline_sections", [])
        missing_sections = [s for s in ["方案详细说明及施工组织设计"] if not re.search(s, text)]
        missing_hints = [h for h in MANDATORY_HINTS if h not in text]

        report = {
            "sections_in_outline": sections,
            "missing_core_sections": missing_sections,
            "missing_keywords": missing_hints,
            "suggestion": "请在方案中明确工期/环保/安全/第三方检测/资料交付等硬性条款的指标与验收口径；若与规格书不一致，请在商务和技术偏差表中列出。"
        }
        
        # 持久化报告
        out = os.path.join("wiki", "sanity_report.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        context["sanity_report_path"] = out
        context["sanity_report"] = report
        
        # 生成检查结果摘要
        issues = []
        if missing_sections:
            issues.append(f"缺少核心章节: {', '.join(missing_sections)}")
        if missing_hints:
            issues.append(f"缺少关键内容: {', '.join(missing_hints)}")
        
        summary = "检查完成，未发现问题" if not issues else f"发现{len(issues)}个问题: {'; '.join(issues)}"
        
        context["current_content"] = summary
        context["current_stage"] = "sanity_check_completed"
        
        return context