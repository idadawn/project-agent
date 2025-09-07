from langgraph.graph import StateGraph, END
from .state import BidState
from agents.structure_extractor import StructureExtractor
from agents.spec_extractor import SpecExtractor
from agents.plan_outliner import PlanOutliner
from agents.bid_assembler import BidAssembler
from agents.sanity_checker import SanityChecker
from agents.solution_optimizer import SolutionOptimizer

def build_bid_graph():
    """构建带用户确认的工作流：结构→[确认]→规格→[确认]→方案→[确认]→拼装→校验"""
    graph = StateGraph(BidState)

    # 创建agent实例
    structure_extractor = StructureExtractor()
    spec_extractor = SpecExtractor()
    plan_outliner = PlanOutliner()
    bid_assembler = BidAssembler()
    sanity_checker = SanityChecker()
    solution_optimizer = SolutionOptimizer()

    # 添加节点
    graph.add_node("structure_extractor", structure_extractor.execute)
    graph.add_node("spec_extractor", spec_extractor.execute)
    # 将“方案提纲”阶段更名为“技术方案”，节点内部仍复用 PlanOutliner 实现
    graph.add_node("technical_solution", plan_outliner.execute)
    graph.add_node("bid_assembler", bid_assembler.execute)
    graph.add_node("sanity_checker", sanity_checker.execute)
    
    # 添加确认节点
    graph.add_node("await_outline_confirmation", _await_outline_confirmation)
    graph.add_node("await_spec_confirmation", _await_spec_confirmation)
    # 新增：等待用户输入技术方案需求
    graph.add_node("await_solution_input", _await_solution_input)
    # 更名：方案确认 → 技术方案确认
    graph.add_node("await_solution_confirmation", _await_solution_confirmation)

    # 设置边（带确认的工作流）
    graph.set_entry_point("structure_extractor")
    graph.add_edge("structure_extractor", "await_outline_confirmation")
    graph.add_conditional_edges("await_outline_confirmation", _check_outline_confirmation, {"spec_extractor": "spec_extractor", "await_outline_confirmation": "await_outline_confirmation"})
    
    graph.add_edge("spec_extractor", "await_spec_confirmation")
    graph.add_conditional_edges(
        "await_spec_confirmation",
        _check_spec_confirmation,
        {"await_solution_input": "await_solution_input", "await_spec_confirmation": "await_spec_confirmation"}
    )
    
    # 用户输入完成后进入“技术方案”节点
    graph.add_conditional_edges(
        "await_solution_input",
        _check_solution_input,
        {"technical_solution": "technical_solution", "await_solution_input": "await_solution_input"}
    )

    graph.add_edge("technical_solution", "await_solution_confirmation")
    graph.add_conditional_edges(
        "await_solution_confirmation",
        _check_solution_confirmation,
        {"solution_optimizer": "solution_optimizer", "await_solution_confirmation": "await_solution_confirmation"}
    )
    
    # 技术方案优化 → 拼装
    graph.add_node("solution_optimizer", solution_optimizer.execute)
    graph.add_edge("solution_optimizer", "bid_assembler")
    
    graph.add_edge("bid_assembler", "sanity_checker")
    graph.add_edge("sanity_checker", END)

    return graph.compile()

def _await_outline_confirmation(state: BidState) -> BidState:
    """等待用户确认招标文件骨架"""
    # 在非交互/默认情况下，自动确认以避免无限循环
    if state.get("auto_confirm", True) and not state.get("interactive", False):
        state["outline_confirmed"] = True
        state["waiting_for_confirmation"] = False
        state["current_step"] = "outline_confirmation_auto"
        return state

    state["waiting_for_confirmation"] = True
    state["current_step"] = "outline_confirmation"
    return state

def _await_spec_confirmation(state: BidState) -> BidState:
    """等待用户确认技术规格书"""
    # 在非交互/默认情况下，自动确认以避免无限循环
    if state.get("auto_confirm", True) and not state.get("interactive", False):
        state["spec_confirmed"] = True
        state["waiting_for_confirmation"] = False
        state["current_step"] = "spec_confirmation_auto"
        return state

    state["waiting_for_confirmation"] = True
    state["current_step"] = "spec_confirmation"
    return state

def _await_solution_confirmation(state: BidState) -> BidState:
    """等待用户确认技术方案"""
    # 在非交互/默认情况下，自动确认以避免无限循环
    if state.get("auto_confirm", True) and not state.get("interactive", False):
        # 复用现有的 plan_confirmed 键，保持向后兼容
        state["plan_confirmed"] = True
        state["waiting_for_confirmation"] = False
        state["current_step"] = "solution_confirmation_auto"
        return state

    state["waiting_for_confirmation"] = True
    state["current_step"] = "solution_confirmation"
    return state

def _await_solution_input(state: BidState) -> BidState:
    """等待用户输入技术方案需求（基于技术规格书与业务需求）"""
    # 非交互模式下尝试自动提供占位输入，避免停滞
    if state.get("auto_confirm", True) and not state.get("interactive", False):
        # 若上游通过 meta 传入了需求，优先采用
        meta = state.get("meta", {}) or {}
        if meta.get("solution_requirements") and not state.get("solution_requirements"):
            state["solution_requirements"] = meta.get("solution_requirements")
        # 兼容：若已有 user_input 则复用
        if not state.get("solution_requirements") and state.get("user_input"):
            state["solution_requirements"] = state.get("user_input")
        # 若仍然没有，提供一个非空占位，允许后续节点继续
        if not state.get("solution_requirements"):
            state["solution_requirements"] = "自动占位：依据技术规格书与通用要求生成默认技术方案草稿"
        state["waiting_for_confirmation"] = False
        state["current_step"] = "solution_input_auto"
        return state

    state["waiting_for_confirmation"] = True
    state["current_step"] = "solution_input"
    return state

def _check_outline_confirmation(state: BidState) -> str:
    """检查招标文件骨架确认状态"""
    if state.get("outline_confirmed", False):
        return "spec_extractor"
    else:
        return "await_outline_confirmation"

def _check_spec_confirmation(state: BidState) -> str:
    """检查技术规格书确认状态"""
    if state.get("spec_confirmed", False):
        return "await_solution_input"
    else:
        return "await_spec_confirmation"

def _check_solution_confirmation(state: BidState) -> str:
    """检查技术方案确认状态（复用 plan_confirmed 键）"""
    if state.get("plan_confirmed", False):
        return "bid_assembler"
    else:
        return "await_solution_confirmation"

def _check_solution_input(state: BidState) -> str:
    """检查是否已获得用户的技术方案输入/需求"""
    # 认为以下任一存在即可进入技术方案生成：
    # 1) solution_requirements（推荐） 2) user_input（兼容）
    if state.get("solution_requirements") or state.get("user_input"):
        return "technical_solution"
    else:
        return "await_solution_input"

# 便捷触发器
def run_build(session_id: str, tender_path: str, wiki_dir="wiki", meta=None, recursion_limit: int = 50, interactive: bool = False, auto_confirm: bool = True):
    """运行最小落地版工作流（同步）"""
    graph = build_bid_graph()
    
    # 创建初始状态（默认开启自动确认，非交互，避免等待导致的循环）
    initial_state = BidState({
        "session_id": session_id,
        "tender_path": tender_path,
        "wiki_dir": wiki_dir,
        "meta": meta or {},
        "project_state": {},
        "auto_confirm": auto_confirm,
        "interactive": interactive,
    })
    
    result = graph.invoke(initial_state, config={"recursion_limit": recursion_limit})
    
    return {
        "outline_path": result.get("outline_path"),
        "spec_path": result.get("spec_path"),
        "plan_path": result.get("plan_path"),
        "plan_draft_path": result.get("plan_draft_path"),
        "draft_path": result.get("draft_path"),
        "sanity_report_path": result.get("sanity_report_path"),
    }

async def run_build_async(session_id: str, uploaded_files: list, wiki_dir="wiki", meta=None, recursion_limit: int = 50, interactive: bool = False, auto_confirm: bool = True):
    """运行最小落地版工作流（异步，保持兼容性）"""
    graph = build_bid_graph()
    
    # 创建初始状态（默认开启自动确认，非交互）
    initial_state = BidState({
        "session_id": session_id,
        "uploaded_files": uploaded_files,
        "wiki_dir": wiki_dir,
        "meta": meta or {},
        "project_state": {},
        "auto_confirm": auto_confirm,
        "interactive": interactive,
    })
    
    result = await graph.ainvoke(initial_state, config={"recursion_limit": recursion_limit})
    
    return {
        "outline_path": result.get("outline_path"),
        "spec_path": result.get("spec_path"),
        "plan_path": result.get("plan_path"),
        "plan_draft_path": result.get("plan_draft_path"),
        "draft_path": result.get("draft_path"),
        "sanity_report_path": result.get("sanity_report_path"),
    }


async def run_build_sequential_async(session_id: str, uploaded_files: list, wiki_dir="wiki", meta=None, interactive: bool = False, auto_confirm: bool = True) -> dict:
    """顺序执行版 A–E 工作流，避免图递归导致的上限问题。"""
    state = BidState({
        "session_id": session_id,
        "uploaded_files": uploaded_files,
        "wiki_dir": wiki_dir,
        "meta": meta or {},
        "project_state": {},
        "auto_confirm": auto_confirm,
        "interactive": interactive,
    })

    # 结构抽取
    state = StructureExtractor().execute(state)
    if interactive and not state.get("outline_confirmed"):
        state["waiting_for_confirmation"] = True
        state["current_step"] = "outline_confirmation"
        return state
    state["outline_confirmed"] = True

    # 规格提取
    state = SpecExtractor().execute(state)
    if interactive and not state.get("spec_confirmed"):
        state["waiting_for_confirmation"] = True
        state["current_step"] = "spec_confirmation"
        return state
    state["spec_confirmed"] = True

    # 方案输入
    if interactive:
        if not state.get("solution_requirements") and not state.get("user_input"):
            state["waiting_for_confirmation"] = True
            state["current_step"] = "solution_input"
            return state
    if state.get("solution_requirements") and not state.get("user_input"):
        state["user_input"] = state["solution_requirements"]
    if not state.get("solution_requirements"):
        state["solution_requirements"] = state.get("user_input") or "自动占位：依据技术规格书与通用要求生成默认技术方案草稿"

    # 技术方案
    state = PlanOutliner().execute(state)
    if interactive and not state.get("plan_confirmed"):
        state["waiting_for_confirmation"] = True
        state["current_step"] = "solution_confirmation"
        return state
    state["plan_confirmed"] = True

    # 拼装与校验
    state = BidAssembler().execute(state)
    state = SanityChecker().execute(state)

    return {
        "outline_path": state.get("outline_path"),
        "spec_path": state.get("spec_path"),
        "plan_path": state.get("plan_path"),
        "plan_draft_path": state.get("plan_draft_path"),
        "draft_path": state.get("draft_path"),
        "sanity_report_path": state.get("sanity_report_path"),
    }