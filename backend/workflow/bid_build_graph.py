from typing import Dict, Any
from langgraph.graph import StateGraph, END
from .state import BidState
from agents.structure_extractor import StructureExtractor
from agents.spec_extractor import SpecExtractor
from agents.plan_outliner import PlanOutliner
from agents.bid_assembler import BidAssembler
from agents.sanity_checker import SanityChecker

def build_bid_graph():
    """构建最小落地版工作流（A–E）：结构→规格→提纲→拼装→校验"""
    graph = StateGraph(BidState)

    # 创建agent实例
    structure_extractor = StructureExtractor()
    spec_extractor = SpecExtractor()
    plan_outliner = PlanOutliner()
    bid_assembler = BidAssembler()
    sanity_checker = SanityChecker()

    # 添加节点
    graph.add_node("structure_extractor", structure_extractor.execute)
    graph.add_node("spec_extractor", spec_extractor.execute)
    graph.add_node("plan_outliner", plan_outliner.execute)
    graph.add_node("bid_assembler", bid_assembler.execute)
    graph.add_node("sanity_checker", sanity_checker.execute)

    # 设置边（新主线）
    graph.set_entry_point("structure_extractor")
    graph.add_edge("structure_extractor", "spec_extractor")
    graph.add_edge("spec_extractor", "plan_outliner")
    graph.add_edge("plan_outliner", "bid_assembler")
    graph.add_edge("bid_assembler", "sanity_checker")
    graph.add_edge("sanity_checker", END)

    return graph.compile()

# 便捷触发器
def run_build(session_id: str, tender_path: str, wiki_dir="wiki", meta=None):
    """运行最小落地版工作流（同步）"""
    graph = build_bid_graph()
    
    # 创建初始状态
    initial_state = BidState({
        "session_id": session_id,
        "tender_path": tender_path,
        "wiki_dir": wiki_dir,
        "meta": meta or {},
        "project_state": {}
    })
    
    result = graph.invoke(initial_state)
    
    return {
        "outline_path": result.get("outline_path"),
        "spec_path": result.get("spec_path"),
        "plan_path": result.get("plan_path"),
        "plan_draft_path": result.get("plan_draft_path"),
        "draft_path": result.get("draft_path"),
        "sanity_report_path": result.get("sanity_report_path"),
    }

async def run_build_async(session_id: str, uploaded_files: list, wiki_dir="wiki", meta=None):
    """运行最小落地版工作流（异步，保持兼容性）"""
    graph = build_bid_graph()
    
    # 创建初始状态
    initial_state = BidState({
        "session_id": session_id,
        "uploaded_files": uploaded_files,
        "wiki_dir": wiki_dir,
        "meta": meta or {},
        "project_state": {}
    })
    
    result = await graph.ainvoke(initial_state)
    
    return {
        "outline_path": result.get("outline_path"),
        "spec_path": result.get("spec_path"),
        "plan_path": result.get("plan_path"),
        "plan_draft_path": result.get("plan_draft_path"),
        "draft_path": result.get("draft_path"),
        "sanity_report_path": result.get("sanity_report_path"),
    }