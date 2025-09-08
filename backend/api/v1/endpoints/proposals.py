# backend/api/v1/endpoints/proposals.py
from fastapi import APIRouter, Body
from workflow.bid_graph import run_build

router = APIRouter(tags=["proposals"])

@router.post("/build")
def build_proposal(payload: dict = Body(...)):
    session_id = payload.get("session_id", "default")
    tender_path = payload.get("tender_path", "uploads/招标文件.md")
    wiki_dir = payload.get("wiki_dir", "wiki")
    meta = payload.get("meta", {})
    result = run_build(session_id, tender_path, wiki_dir, meta)
    return {
        "ok": True,
        "outline_path": result.get("outline_path"),
        "spec_path": result.get("spec_path"),
    }
