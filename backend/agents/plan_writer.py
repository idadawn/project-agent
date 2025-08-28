from typing import Dict, Any
import os, datetime
from .base import BaseAgent

PROMPT = """
你是投标方案撰写器。将下述“方案草稿”按“技术规格书（提取）”逐条充实：
- 对每个小节，补充：承诺、实现路径、量化指标（如排放/能效/交付份数/检验流程）、交付件。
- 在段末添加：证据绑定：§x.x（若无法定位，留空）。
- 对应评分项标注：技术方案/施工方法。
- 避免大段虚写，保持简明要点。

【技术规格书（提取，节选）】
{SPEC}

【方案草稿（待充实）】
{DRAFT}
"""

class PlanWriter(BaseAgent):
    def __init__(self):
        super().__init__("plan_writer")
    
    def get_system_prompt(self) -> str:
        return "你是一个严格按技术规格书逐条响应、并对齐评分点的投标方案撰写专家。"

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        wiki_dir = state.get("wiki_dir", "wiki")
        spec_path = state.get("spec_path")
        draft_path = state.get("plan_draft_path")
        out_path = draft_path or os.path.join(wiki_dir, "方案_草稿.md")

        spec = ""
        if spec_path and os.path.exists(spec_path):
            with open(spec_path, "r", encoding="utf-8") as f:
                spec = f.read()[:12000]
        draft = ""
        if draft_path and os.path.exists(draft_path):
            with open(draft_path, "r", encoding="utf-8") as f:
                draft = f.read()[:12000]

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": PROMPT.format(SPEC=spec, DRAFT=draft)}
        ]

        enriched = None
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            enriched = loop.run_until_complete(self.llm_client.generate(messages))
            loop.close()
        except Exception as e:
            print(f"PlanWriter LLM失败，保留原草稿: {e}")

        if not enriched or not enriched.strip():
            enriched = draft or "# 方案详细说明及施工组织设计\n\n> 待填充（PlanWriter未生成内容）\n"

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(enriched)

        state["plan_draft_path"] = out_path
        return state

