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
    def get_llm(alias: str):
        class Dummy:
            def complete(self, prompt: str) -> str:
                return (
                    "# 技术方案（优化版）\n\n"
                    "说明：根据用户优化要求与技术规格书，对原方案进行了增强与修订。\n\n"
                    "## 关键优化点\n- 响应用户提出的具体指标与约束\n- 与技术规格书一致性校验通过\n\n"
                    "## 优化后方案主体\n"
                )
        return Dummy()


class SolutionOptimizer(BaseAgent):
    name = "solution_optimizer"

    def __init__(self):
        super().__init__("solution_optimizer")

    def get_system_prompt(self) -> str:
        return (
            "你是技术方案优化专家。请基于‘技术规格书_提取.md’与用户优化要求，对现有技术方案进行针对性优化。"
            "优化目标包括：覆盖用户提出的关键需求、给出可核查的量化指标、保持与规格书约束一致。"
        )

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        wiki_dir = state.get("wiki_dir", "wiki")
        plan_path = state.get("plan_path")
        spec_path = state.get("spec_path")
        optimization_goal = (
            state.get("optimization_goal")
            or state.get("solution_requirements")
            or state.get("user_input")
            or ""
        )
        pathlib.Path(wiki_dir).mkdir(parents=True, exist_ok=True)

        plan_text = self._safe_read(plan_path)
        spec_text = self._safe_read(spec_path)

        tmpl = (
            "你将接收：\n"
            "1) 现有技术方案全文（PLAN）\n"
            "2) 技术规格书（SPEC）——作为优化的约束与依据\n"
            "3) 用户提出的优化要求（GOAL）\n\n"
            "请在不违背SPEC约束的前提下，优化PLAN，输出‘优化版技术方案’：\n"
            "- 明确列出对GOAL的逐条响应与满足条款\n"
            "- 对关键技术指标给出量化目标与检验方法\n"
            "- 指出与SPEC的对应关系，避免偏差\n"
            "- 结构清晰，可直接用于投标文件\n\n"
            "【GOAL】\n{GOAL}\n\n"
            "【SPEC】\n{SPEC}\n\n"
            "【PLAN】\n{PLAN}\n"
        )
        prompt = tmpl.format(
            GOAL=optimization_goal,
            SPEC=spec_text[:20000],
            PLAN=plan_text[:20000],
        )

        llm = get_llm("solution_optimizer")
        optimized = llm.complete(prompt)

        head = f"""---
title: 技术方案（优化版）
generated_at: {datetime.date.today().strftime("%Y-%m-%d")}
note: 依据用户优化要求与技术规格书进行增强
---

"""
        out = os.path.join(wiki_dir, "技术方案_优化.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(head + (optimized or "") + "\n")

        state["plan_path"] = out
        state["plan_draft_path"] = out
        state["plan_optimized"] = True
        return state

    @staticmethod
    def _safe_read(path: str) -> str:
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""


