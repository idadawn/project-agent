# backend/workflow/bid_graph.py
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from agents.structure_extractor import StructureExtractor
from agents.spec_extractor import SpecExtractor
from agents.plan_outliner import PlanOutliner
from agents.bid_assembler import BidAssembler
from agents.sanity_checker import SanityChecker

def build_bid_graph(State=dict):
    graph = StateGraph(State)

    graph.add_node("structure_extractor", StructureExtractor().execute)
    graph.add_node("spec_extractor", SpecExtractor().execute)
    graph.add_node("plan_outliner", PlanOutliner().execute)
    graph.add_node("bid_assembler", BidAssembler().execute)
    graph.add_node("sanity_checker", SanityChecker().execute)

    graph.set_entry_point("structure_extractor")
    graph.add_edge("structure_extractor", "spec_extractor")
    graph.add_edge("spec_extractor", "plan_outliner")
    graph.add_edge("plan_outliner", "bid_assembler")
    graph.add_edge("bid_assembler", "sanity_checker")
    graph.add_edge("sanity_checker", END)
    return graph.compile()

def run_build(session_id: str, tender_path: str, wiki_dir="wiki", meta=None) -> Dict[str, Any]:
    graph = build_bid_graph()
    state: Dict[str, Any] = {
        "session_id": session_id,
        "tender_path": tender_path,
        "wiki_dir": wiki_dir,
        "meta": meta or {}
    }
    return graph.invoke(state)
