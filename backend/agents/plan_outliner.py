from typing import Dict, Any
import os, pathlib, datetime
from .base import BaseAgent

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "plan_outliner.md")

class PlanOutliner(BaseAgent):
    def __init__(self):
        super().__init__("plan_outliner")
    
    def get_system_prompt(self) -> str:
        return """你是一个投标方案总工。基于技术规格书和投标文件格式要求，生成详细的方案提纲。"""

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """同步执行方法，用于LangGraph工作流"""
        wiki_dir = state.get("wiki_dir", "wiki")
        spec_path = state.get("spec_path")
        sections = state.get("outline_sections", [])
        meta = state.get("meta", {})
        
        pathlib.Path(wiki_dir).mkdir(parents=True, exist_ok=True)

        spec = ""
        if spec_path and os.path.exists(spec_path):
            with open(spec_path, "r", encoding="utf-8") as f:
                spec = f.read()
        
        # 读取prompt模板
        prompt_tmpl = ""
        if os.path.exists(PROMPT_PATH):
            with open(PROMPT_PATH, "r", encoding="utf-8") as f:
                prompt_tmpl = f.read()
        else:
            prompt_tmpl = self._get_default_prompt()

        prompt = prompt_tmpl.format(
            PROJECT_NAME = meta.get("project_name", "{{PROJECT_NAME}}"),
            SPEC = spec[:12000],       # 截断保护
            FORMAT_SECTIONS = "\n".join(f"- {s}" for s in sections) if sections else "",
        )
        
        # 使用LLM生成提纲
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        # 同步调用LLM（失败则回退默认提纲）
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            outline = loop.run_until_complete(self.llm_client.generate(messages))
            loop.close()
        except Exception as e:
            print(f"LLM调用失败，使用默认提纲: {e}")
            outline = self._fallback_outline()
        
        if not outline.strip():
            outline = self._fallback_outline()

        head = f"""---
 title: 方案（提纲）
 generated_at: {datetime.date.today().strftime("%Y-%m-%d")}
 ---
 
 """
        
        outline_path = os.path.join(wiki_dir, "方案_提纲.md")
        with open(outline_path, "w", encoding="utf-8") as f:
            f.write(head + outline + "\n")
        
        # 方案草稿初稿（与提纲等价，后续由PlanWriter充实）
        draft_head = f"""---
 title: 方案（草稿）
 generated_at: {datetime.date.today().strftime("%Y-%m-%d")}
 note: 由 PlanOutliner 生成的初稿（待 PlanWriter 充实）
 ---
 
 """
        draft_path = os.path.join(wiki_dir, "方案_草稿.md")
        with open(draft_path, "w", encoding="utf-8") as f:
            f.write(draft_head + outline + "\n")
        
        state["plan_path"] = outline_path
        state["plan_draft_path"] = draft_path
        return state

    async def execute_async(self, context: Any) -> Any:
        """保持原有的异步接口兼容性"""
        wiki_dir = "wiki"
        spec_path = context.get("spec_path")
        sections = context.get("outline_sections", [])
        
        pathlib.Path(wiki_dir).mkdir(parents=True, exist_ok=True)

        spec = ""
        if spec_path and os.path.exists(spec_path):
            with open(spec_path, "r", encoding="utf-8") as f:
                spec = f.read()
        
        # 读取prompt模板
        prompt_tmpl = ""
        if os.path.exists(PROMPT_PATH):
            with open(PROMPT_PATH, "r", encoding="utf-8") as f:
                prompt_tmpl = f.read()
        else:
            prompt_tmpl = self._get_default_prompt()

        prompt = prompt_tmpl.format(
            PROJECT_NAME = context.get("project_name", "{{PROJECT_NAME}}"),
            SPEC = spec[:12000],       # 截断保护
            FORMAT_SECTIONS = "\n".join(f"- {s}" for s in sections) if sections else "",
        )
        
        # 使用LLM生成提纲
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        outline = await self.llm_client.generate(messages)
        
        if not outline.strip():
            outline = self._fallback_outline()

        head = f"""---
 title: 方案（提纲）
 generated_at: {datetime.date.today().strftime("%Y-%m-%d")}
 ---
 
 """
        
        out = os.path.join(wiki_dir, "方案_提纲.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(head + outline + "\n")
        
        # 方案草稿初稿
        draft_head = f"""---
 title: 方案（草稿）
 generated_at: {datetime.date.today().strftime("%Y-%m-%d")}
 note: 由 PlanOutliner 生成的初稿（待 PlanWriter 充实）
 ---
 
 """
        draft_path = os.path.join(wiki_dir, "方案_草稿.md")
        with open(draft_path, "w", encoding="utf-8") as f:
            f.write(draft_head + outline + "\n")
        
        context["plan_path"] = out
        context["plan_draft_path"] = draft_path
        context["current_content"] = "成功生成方案提纲与草稿"
        context["current_stage"] = "plan_outlining_completed"
        
        return context

    @staticmethod
    def _fallback_outline()->str:
        return (
        "# 方案详细说明及施工组织设计\n\n"
        "## A. 技术方案（25分）\n"
        "- 项目理解与技术路线\n- 关键设备与参数\n- 排放与能效保证值\n- 系统集成与接口\n- 控制与数字化\n\n"
        "## B. 施工方法及主要技术措施（25分）\n"
        "- 组织机构与职责\n- 关键工序与质量控制\n- 干扰最小化与应急回退\n- 安全文明与环保\n- 试车与验收\n\n"
        "## C. 进度与资源\n- 工期里程碑\n- 人材机配置\n\n"
        "## D. 质量/HSE/风险\n- 质量目标与流程\n- 风险矩阵与缓解\n\n"
        "## E. 资料与培训\n- 资料清单与份数\n- 培训与考核\n"
        )

    def _get_default_prompt(self) -> str:
        return """你是投标方案总工。目标：基于**技术规格书**与**投标文件格式**，输出"方案详细说明及施工组织设计"的**三级标题提纲 + 每节检查点**，
并让提纲可直接映射到评分项（技术方案25分、施工方法与主要技术措施25分）。

【项目】{PROJECT_NAME}

【已抽取技术规格书（节选）】
{SPEC}

【投标文件格式章节（提取）】
{FORMAT_SECTIONS}

【要求】
1) 生成 Markdown，层级不超过三级。
2) 每个小节末尾使用"证据绑定：规格书 §x.x（若无则留空）"。
3) 明确"工期/环保/安全/第三方检测/资料交付/验收口径"的检查点。
4) 不生成大段正文，只列纲要+checklist。"""