# backend/agents/plan_outliner.py
from typing import Dict, Any
import os, pathlib, datetime

try:
    from .base import BaseAgent
except Exception:
    class BaseAgent:
        name = "base"
        def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
            return state

try:
    from app_core.llm_client import get_llm
except Exception:
    def get_llm(alias:str):
        class Dummy:
            def complete(self, prompt:str)->str:
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
        return Dummy()

try:
    from utils.proposal_outline import extract_proposal_outline, generate_proposal_markdown
except ImportError:
    # Fallback for when utils module is not available
    def extract_proposal_outline(text: str, outline_sections: List[str] = None) -> Dict[str, List[str]]:
        return {"main_sections": [], "sub_sections": {}}
    
    def generate_proposal_markdown(outline: Dict[str, List[str]], title: str = "技术方案提案") -> str:
        return f"# {title}\n\n*方案提纲生成功能不可用*\n"

PROMPT_FILE = os.path.join(os.path.dirname(__file__), "..", "prompts", "plan_outliner.md")

class PlanOutliner(BaseAgent):
    name = "plan_outliner"

    def __init__(self):
        super().__init__("plan_outliner")

    def get_system_prompt(self) -> str:
        return "你是方案提纲生成专家，根据技术规格书生成技术方案和施工方法的详细提纲。"

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        wiki_dir = state.get("wiki_dir", "wiki")
        spec_path = state.get("spec_path")
        tender_path = state.get("tender_path")
        sections = state.get("outline_sections", [])
        meta = state.get("meta", {})
        pathlib.Path(wiki_dir).mkdir(parents=True, exist_ok=True)

        # 首先尝试从招标文件中提取方案提纲结构
        tender_text = ""
        if tender_path and os.path.exists(tender_path):
            with open(tender_path, "r", encoding="utf-8") as f:
                tender_text = f.read()
        
        # 使用改进的方案提纲提取
        proposal_outline = extract_proposal_outline(tender_text, sections)
        
        spec_text = ""
        if spec_path and os.path.exists(spec_path):
            with open(spec_path, "r", encoding="utf-8") as f:
                spec_text = f.read()

        # 如果自动提取的提纲为空或过于简单，使用LLM生成
        if not proposal_outline["main_sections"] or len(proposal_outline["main_sections"]) < 2:
            tmpl = ""
            if os.path.exists(PROMPT_FILE):
                with open(PROMPT_FILE, "r", encoding="utf-8") as f:
                    tmpl = f.read()
            else:
                tmpl = (
                    "你是投标方案总工。目标：基于技术规格书与投标文件格式，输出方案的三级提纲与检查点。"
                    "要求：Markdown、证据绑定、不要生成大段正文。"
                    "\n\n【技术规格书】\n{SPEC}\n\n【格式章节】\n{FORMAT_SECTIONS}\n"
                )

            prompt = tmpl.format(
                PROJECT_NAME = meta.get("project_name", "{{PROJECT_NAME}}"),
                SPEC = spec_text[:12000],
                FORMAT_SECTIONS = "\n".join(f"- {s}" for s in sections) if sections else "",
            )

            llm = get_llm("plan_outliner")
            outline_content = llm.complete(prompt)
        else:
            # 使用自动提取的提纲生成Markdown
            project_name = meta.get("project_name", "技术方案")
            outline_content = generate_proposal_markdown(proposal_outline, f"{project_name}方案详细说明及施工组织设计")

        head = f"""---
title: 方案（提纲）
generated_at: {datetime.date.today().strftime("%Y-%m-%d")}
---

"""
        out = os.path.join(wiki_dir, "方案_提纲.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(head + (outline_content or "") + "\n")
        state["plan_path"] = out
        return state
