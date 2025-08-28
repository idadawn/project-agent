from typing import Dict, Any
import os, pathlib, datetime
from .base import BaseAgent

class BidAssembler(BaseAgent):
    def __init__(self):
        super().__init__("bid_assembler")
    
    def get_system_prompt(self) -> str:
        return """你是一个投标文件组装专家。负责将各个部分组合成完整的投标文件草案。"""

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """同步执行方法，用于LangGraph工作流"""
        wiki_dir = state.get("wiki_dir", "wiki")
        outline_path = state.get("outline_path")
        plan_path = state.get("plan_path")
        spec_path = state.get("spec_path")

        outline = ""
        if outline_path and os.path.exists(outline_path):
            with open(outline_path, "r", encoding="utf-8") as f:
                outline = f.read()
        
        plan = ""
        if plan_path and os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as f:
                plan = f.read()
        
        spec = ""
        if spec_path and os.path.exists(spec_path):
            with open(spec_path, "r", encoding="utf-8") as f:
                spec = f.read()

        assembled = self._merge(outline, plan, spec)
        out = os.path.join(wiki_dir, "投标文件_草案.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(assembled)
        
        state["draft_path"] = out
        return state

    async def execute_async(self, context: Any) -> Any:
        """保持原有的异步接口兼容性"""
        wiki_dir = "wiki"
        outline_path = context.get("outline_path")
        plan_path = context.get("plan_path")
        spec_path = context.get("spec_path")

        outline = ""
        if outline_path and os.path.exists(outline_path):
            with open(outline_path, "r", encoding="utf-8") as f:
                outline = f.read()
        
        plan = ""
        if plan_path and os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as f:
                plan = f.read()
        
        spec = ""
        if spec_path and os.path.exists(spec_path):
            with open(spec_path, "r", encoding="utf-8") as f:
                spec = f.read()

        assembled = self._merge(outline, plan, spec)
        out = os.path.join(wiki_dir, "投标文件_草案.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(assembled)
        
        context["draft_path"] = out
        context["current_content"] = "成功组装投标文件草案"
        context["current_stage"] = "bid_assembly_completed"
        
        return context

    def _merge(self, outline:str, plan:str, spec:str)->str:
        today = datetime.date.today().strftime("%Y-%m-%d")
        return f"""---
title: 投标文件（草案）
generated_at: {today}
note: 自动拼装：骨架 + 方案提纲（其余章节留占位）
---

{outline}

---

### 附：技术规格书（提取节选）
> 供方案引用与一致性检查

{spec[:20000]}
"""