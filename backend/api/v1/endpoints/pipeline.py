"""
Pipeline API endpoints for A–E workflow execution (interactive and non-interactive)
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio
from datetime import datetime

from workflow.bid_build_graph import run_build_async, run_build_sequential_async
from agents.structure_extractor import StructureExtractor
from agents.spec_extractor import SpecExtractor
from agents.plan_outliner import PlanOutliner
from agents.bid_assembler import BidAssembler
from agents.sanity_checker import SanityChecker


router = APIRouter()


# ===== In-memory session store (可替换为 Redis/DB) =====
SESSION_STORE: Dict[str, Dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _ensure_session(session_id: Optional[str]) -> str:
    import uuid
    sid = session_id or f"sess-{uuid.uuid4().hex[:12]}"
    SESSION_STORE.setdefault(sid, {"created_at": _now_iso(), "updated_at": _now_iso()})
    return sid


def _summarize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "outline_path": state.get("outline_path"),
        "spec_path": state.get("spec_path"),
        "plan_path": state.get("plan_path"),
        "plan_draft_path": state.get("plan_draft_path"),
        "draft_path": state.get("draft_path"),
        "sanity_report_path": state.get("sanity_report_path"),
        "outline_confirmed": state.get("outline_confirmed"),
        "spec_confirmed": state.get("spec_confirmed"),
        "plan_confirmed": state.get("plan_confirmed"),
        "current_step": state.get("current_step"),
        "waiting_for_confirmation": state.get("waiting_for_confirmation", False),
    }


class StartWorkflowRequest(BaseModel):
    session_id: Optional[str] = None
    tender_path: Optional[str] = None
    uploaded_files: Optional[List[Dict[str, Any]]] = None
    wiki_dir: Optional[str] = "wiki"
    meta: Optional[Dict[str, Any]] = None
    interactive: bool = False
    auto_confirm: bool = True
    recursion_limit: int = 50
    solution_requirements: Optional[str] = None
    user_input: Optional[str] = None


class StartWorkflowResponse(BaseModel):
    success: bool
    session_id: str
    message: str
    state: Dict[str, Any]


class ContinueWorkflowRequest(BaseModel):
    session_id: str
    outline_confirmed: Optional[bool] = None
    spec_confirmed: Optional[bool] = None
    plan_confirmed: Optional[bool] = None
    solution_requirements: Optional[str] = None
    user_input: Optional[str] = None


class ContinueWorkflowResponse(BaseModel):
    success: bool
    session_id: str
    message: str
    state: Dict[str, Any]


async def _run_interactive_until_pause(state: Dict[str, Any]) -> Dict[str, Any]:
    """顺序执行各个 agent；遇到需要确认或输入时暂停返回当前状态。"""
    interactive = state.get("interactive", False)

    # 1) 结构抽取
    if not state.get("outline_path"):
        state = StructureExtractor().execute(state)

    # 1.1) 确认骨架
    if interactive and not state.get("outline_confirmed"):
        state["waiting_for_confirmation"] = True
        state["current_step"] = "outline_confirmation"
        return state
    state["outline_confirmed"] = True
    state["waiting_for_confirmation"] = False

    # 2) 规格提取
    if not state.get("spec_path"):
        state = SpecExtractor().execute(state)

    # 2.1) 确认规格书
    if interactive and not state.get("spec_confirmed"):
        state["waiting_for_confirmation"] = True
        state["current_step"] = "spec_confirmation"
        return state
    state["spec_confirmed"] = True
    state["waiting_for_confirmation"] = False

    # 3) 等待方案输入
    if interactive:
        if not state.get("solution_requirements") and not state.get("user_input"):
            state["waiting_for_confirmation"] = True
            state["current_step"] = "solution_input"
            return state

    # 3.1) 兼容：将 solution_requirements 映射到 user_input
    if state.get("solution_requirements") and not state.get("user_input"):
        state["user_input"] = state["solution_requirements"]

    # 4) 技术方案生成（PlanOutliner 复用）
    if not state.get("plan_path"):
        state = PlanOutliner().execute(state)

    # 4.1) 确认技术方案
    if interactive and not state.get("plan_confirmed"):
        state["waiting_for_confirmation"] = True
        state["current_step"] = "solution_confirmation"
        return state
    state["plan_confirmed"] = True
    state["waiting_for_confirmation"] = False

    # 5) 拼装与校验
    if not state.get("draft_path"):
        state = BidAssembler().execute(state)

    if not state.get("sanity_report_path"):
        state = SanityChecker().execute(state)

    state["current_step"] = "completed"
    return state


@router.post("/workflow/start", response_model=StartWorkflowResponse)
async def start_workflow(request: StartWorkflowRequest):
    try:
        session_id = _ensure_session(request.session_id)
        state: Dict[str, Any] = SESSION_STORE.get(session_id, {}).copy()

        # 初始化状态
        state.update({
            "session_id": session_id,
            "tender_path": request.tender_path,
            "uploaded_files": request.uploaded_files or [],
            "wiki_dir": request.wiki_dir or "wiki",
            "meta": request.meta or {},
            "interactive": bool(request.interactive),
            "auto_confirm": bool(request.auto_confirm),
        })
        if request.solution_requirements and not state.get("solution_requirements"):
            state["solution_requirements"] = request.solution_requirements
        if request.user_input and not state.get("user_input"):
            state["user_input"] = request.user_input

        # 非交互：直接跑完整 A–E（顺序执行，避免图递归）
        if not request.interactive and request.auto_confirm:
            result = await run_build_sequential_async(
                session_id=session_id,
                uploaded_files=state.get("uploaded_files", []),
                wiki_dir=state.get("wiki_dir", "wiki"),
                meta=state.get("meta", {}),
                interactive=False,
                auto_confirm=True,
            )
            state.update(result)
            state["current_step"] = "completed"
        else:
            # 交互：逐步推进，遇到需要确认/输入则暂停
            state = await _run_interactive_until_pause(state)

        state["updated_at"] = _now_iso()
        SESSION_STORE[session_id] = state

        return StartWorkflowResponse(
            success=True,
            session_id=session_id,
            message="工作流已启动",
            state=_summarize_state(state),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")


@router.post("/workflow/continue", response_model=ContinueWorkflowResponse)
async def continue_workflow(request: ContinueWorkflowRequest):
    try:
        if request.session_id not in SESSION_STORE:
            raise HTTPException(status_code=404, detail="会话不存在")

        state = SESSION_STORE[request.session_id]

        # 应用用户确认或输入
        if request.outline_confirmed is not None:
            state["outline_confirmed"] = bool(request.outline_confirmed)
        if request.spec_confirmed is not None:
            state["spec_confirmed"] = bool(request.spec_confirmed)
        if request.plan_confirmed is not None:
            state["plan_confirmed"] = bool(request.plan_confirmed)
        if request.solution_requirements:
            state["solution_requirements"] = request.solution_requirements
        if request.user_input:
            state["user_input"] = request.user_input

        # 推进
        state = await _run_interactive_until_pause(state)
        state["updated_at"] = _now_iso()
        SESSION_STORE[request.session_id] = state

        return ContinueWorkflowResponse(
            success=True,
            session_id=request.session_id,
            message="工作流已推进",
            state=_summarize_state(state),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推进失败: {str(e)}")


@router.get("/workflow/status/{session_id}")
async def workflow_status(session_id: str):
    try:
        if session_id not in SESSION_STORE:
            raise HTTPException(status_code=404, detail="会话不存在")
        state = SESSION_STORE[session_id]
        return {
            "success": True,
            "session_id": session_id,
            "state": _summarize_state(state),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")