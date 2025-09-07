from langgraph.graph import StateGraph, END
from .state import BidState
from agents.structure_extractor import StructureExtractor
from agents.spec_extractor import SpecExtractor


def build_bid_graph():
    """构建简化版工作流：结构抽取→规格提取"""
    graph = StateGraph(BidState)

    structure_extractor = StructureExtractor()
    spec_extractor = SpecExtractor()

    graph.add_node("structure_extractor", structure_extractor.execute)
    graph.add_node("spec_extractor", spec_extractor.execute)

    graph.add_node("await_outline_confirmation", _await_outline_confirmation)
    graph.add_node("await_spec_confirmation", _await_spec_confirmation)

    graph.set_entry_point("structure_extractor")
    graph.add_edge("structure_extractor", "await_outline_confirmation")
    graph.add_conditional_edges(
        "await_outline_confirmation",
        _check_outline_confirmation,
        {"spec_extractor": "spec_extractor", "await_outline_confirmation": "await_outline_confirmation"},
    )

    graph.add_edge("spec_extractor", "await_spec_confirmation")
    graph.add_conditional_edges(
        "await_spec_confirmation",
        _check_spec_confirmation,
        {END: END, "await_spec_confirmation": "await_spec_confirmation"},
    )

    return graph.compile()


def _await_outline_confirmation(state: BidState) -> BidState:
    """等待用户确认招标文件骨架"""
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
    if state.get("auto_confirm", True) and not state.get("interactive", False):
        state["spec_confirmed"] = True
        state["waiting_for_confirmation"] = False
        state["current_step"] = "spec_confirmation_auto"
        return state

    state["waiting_for_confirmation"] = True
    state["current_step"] = "spec_confirmation"
    return state


def _check_outline_confirmation(state: BidState) -> str:
    """检查招标文件骨架确认状态"""
    if state.get("outline_confirmed", False):
        return "spec_extractor"
    return "await_outline_confirmation"


def _check_spec_confirmation(state: BidState) -> str:
    """检查技术规格书确认状态"""
    if state.get("spec_confirmed", False):
        return END
    return "await_spec_confirmation"


# 便捷触发器
def run_build(session_id: str, tender_path: str, wiki_dir="wiki", meta=None, recursion_limit: int = 50, interactive: bool = False, auto_confirm: bool = True):
    """运行简化版工作流（同步）"""
    graph = build_bid_graph()
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
    }


async def run_build_async(session_id: str, uploaded_files: list, wiki_dir="wiki", meta=None, recursion_limit: int = 50, interactive: bool = False, auto_confirm: bool = True):
    """运行简化版工作流（异步，保持兼容性）"""
    graph = build_bid_graph()
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
    }


async def run_build_sequential_async(session_id: str, uploaded_files: list, wiki_dir="wiki", meta=None, interactive: bool = False, auto_confirm: bool = True) -> dict:
    """顺序执行版工作流，避免图递归导致的上限问题。"""
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

    return {
        "outline_path": state.get("outline_path"),
        "spec_path": state.get("spec_path"),
    }
