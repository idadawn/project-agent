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
                    "# 技术方案详细说明\n\n"
                    "## 1. 项目概述\n"
                    "本项目旨在提供完整的技术解决方案，包括系统设计、设备选型、施工组织、质量控制和安全管理等方面。\n\n"
                    "## 2. 技术方案设计\n"
                    "### 2.1 总体技术路线\n"
                    "采用先进成熟的技术路线，确保系统稳定性、可靠性和经济性。主要技术特点包括：\n"
                    "- 模块化设计，便于安装和维护\n"
                    "- 智能化控制，实现自动化运行\n"
                    "- 节能环保，符合国家排放标准\n\n"
                    "### 2.2 关键设备选型\n"
                    "选用国内外知名品牌设备，确保设备性能和质量：\n"
                    "- 主机设备：采用XX品牌，功率XXkW，效率XX%\n"
                    "- 控制系统：采用PLC+触摸屏控制，支持远程监控\n"
                    "- 辅助设备：配套完善的检测和保护装置\n\n"
                    "## 3. 施工组织设计\n"
                    "### 3.1 施工组织机构\n"
                    "成立专业的项目管理团队，明确各岗位职责：\n"
                    "- 项目经理：全面负责项目协调和管理\n"
                    "- 技术负责人：负责技术方案实施和质量控制\n"
                    "- 安全负责人：负责施工现场安全管理\n\n"
                    "### 3.2 施工方法和工序\n"
                    "采用科学的施工方法，确保工程质量和进度：\n"
                    "1. 基础施工：严格按照设计图纸进行\n"
                    "2. 设备安装：专业团队进行设备就位和调试\n"
                    "3. 系统调试：全面测试系统性能和稳定性\n\n"
                    "## 4. 质量保证措施\n"
                    "建立完善的质量管理体系：\n"
                    "- 严格执行ISO9001质量管理标准\n"
                    "- 关键工序设置质量控制点\n"
                    "- 定期进行质量检查和评估\n\n"
                    "## 5. 安全文明施工\n"
                    "确保施工现场安全文明：\n"
                    "- 制定详细的安全施工方案\n"
                    "- 配备完善的安全防护设施\n"
                    "- 定期进行安全培训和检查\n"
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
        return "你是技术方案编写专家，根据技术规格书和用户要求编写详细的技术方案内容。"

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

        # 获取用户输入的技术要求
        user_input = state.get("user_input", "")
        
        # 生成技术方案内容（不再是提纲）
        tmpl = ""
        if os.path.exists(PROMPT_FILE):
            with open(PROMPT_FILE, "r", encoding="utf-8") as f:
                tmpl = f.read()
        else:
            tmpl = (
                "你是投标方案总工。目标：基于技术规格书、招标文件要求和用户输入，编写详细的技术方案内容。"
                "要求：详细的技术描述、实施方案、质量控制措施、安全措施等具体内容。"
                "\n\n【项目名称】\n{PROJECT_NAME}\n\n"
                "【用户要求】\n{USER_INPUT}\n\n"
                "【技术规格书】\n{SPEC}\n\n"
                "【格式章节】\n{FORMAT_SECTIONS}\n"
            )

        prompt = tmpl.format(
            PROJECT_NAME = meta.get("project_name", "{{PROJECT_NAME}}"),
            USER_INPUT = user_input,
            SPEC = spec_text[:12000],
            FORMAT_SECTIONS = "\n".join(f"- {s}" for s in sections) if sections else "",
        )

        llm = get_llm("plan_outliner")
        outline_content = llm.complete(prompt)

        head = f"""---
title: 技术方案
generated_at: {datetime.date.today().strftime("%Y-%m-%d")}
---

"""
        out = os.path.join(wiki_dir, "技术方案.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(head + (outline_content or "") + "\n")
        state["plan_path"] = out
        return state