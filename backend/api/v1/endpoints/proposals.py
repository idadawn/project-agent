from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from services.session_manager import SessionManager, get_session_manager
from workflow.bid_build_graph import run_build, run_build_async

router = APIRouter()


class ProposalSummary(BaseModel):
    session_id: str
    title: str
    created_at: str
    updated_at: str
    word_count: int
    sections_count: int
    status: str  # "draft", "completed", "in_progress"


class ProposalDetail(BaseModel):
    session_id: str
    title: str
    plan: str
    content: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class BuildProposalRequest(BaseModel):
    session_id: str
    tender_path: str  # 招标文件路径，如 "uploads/招标文件.md"
    wiki_dir: str = "wiki"  # 输出目录
    meta: Optional[Dict[str, Any]] = None  # 项目元数据


class BuildProposalResponse(BaseModel):
    ok: bool
    outline_path: Optional[str] = None
    spec_path: Optional[str] = None
    plan_path: Optional[str] = None
    plan_draft_path: Optional[str] = None
    final_bid_path: Optional[str] = None
    diff_table_path: Optional[str] = None
    qa_report_path: Optional[str] = None
    # legacy
    draft_path: Optional[str] = None
    sanity_report: Optional[Dict[str, Any]] = None
    sanity_report_path: Optional[str] = None
    message: str = ""


@router.post("/build", response_model=BuildProposalResponse)
async def build_proposal(request: BuildProposalRequest):
    """触发A-G工作流，生成投标文件"""
    try:
        result = run_build(
            session_id=request.session_id,
            tender_path=request.tender_path,
            wiki_dir=request.wiki_dir,
            meta=request.meta
        )
        
        return BuildProposalResponse(
            ok=True,
            outline_path=result.get("outline_path"),
            spec_path=result.get("spec_path"),
            plan_path=result.get("plan_path"),
            plan_draft_path=result.get("plan_draft_path"),
            final_bid_path=result.get("final_bid_path"),
            diff_table_path=result.get("diff_table_path"),
            qa_report_path=result.get("qa_report_path"),
            draft_path=result.get("draft_path"),
            sanity_report=result.get("sanity_report"),
            sanity_report_path=result.get("sanity_report_path"),
            message="投标文件生成成功"
        )
        
    except Exception as e:
        return BuildProposalResponse(
            ok=False,
            message=f"投标文件生成失败: {str(e)}"
        )


@router.post("/build_async", response_model=BuildProposalResponse)
async def build_proposal_async(request: BuildProposalRequest):
    """异步触发A-G工作流，生成投标文件（保持兼容性）"""
    try:
        result = run_build(
            session_id=request.session_id,
            tender_path=request.tender_path,
            wiki_dir=request.wiki_dir,
            meta=request.meta
        )
        
        return BuildProposalResponse(
            ok=True,
            outline_path=result.get("outline_path"),
            spec_path=result.get("spec_path"),
            plan_path=result.get("plan_path"),
            plan_draft_path=result.get("plan_draft_path"),
            final_bid_path=result.get("final_bid_path"),
            diff_table_path=result.get("diff_table_path"),
            qa_report_path=result.get("qa_report_path"),
            draft_path=result.get("draft_path"),
            sanity_report=result.get("sanity_report"),
            sanity_report_path=result.get("sanity_report_path"),
            message="投标文件生成成功"
        )
        
    except Exception as e:
        return BuildProposalResponse(
            ok=False,
            message=f"投标文件生成失败: {str(e)}"
        )


@router.get("/list", response_model=List[ProposalSummary])
async def list_proposals(
    session_manager: SessionManager = Depends(get_session_manager)
):
    try:
        sessions = session_manager.list_sessions()
        proposals = []
        
        for session_id, session_data in sessions.items():
            # Only include sessions that have proposals
            if not session_data.get("current_content") and not session_data.get("plan"):
                continue
            
            # Extract title from plan
            plan = session_data.get("plan", "")
            title = "Untitled Proposal"
            if plan:
                lines = plan.split('\n')
                for line in lines:
                    if line.strip().startswith('#'):
                        title = line.strip('#').strip()
                        break
            
            # Determine status
            status = "draft"
            if session_data.get("current_content"):
                status = "completed"
            elif session_data.get("plan"):
                status = "in_progress"
            
            # Count sections and words
            content = session_data.get("current_content", "")
            sections_count = len([line for line in content.split('\n') if line.strip().startswith('#')])
            word_count = len(content.split())
            
            proposals.append(ProposalSummary(
                session_id=session_id,
                title=title,
                created_at=session_data.get("created_at", ""),
                updated_at=session_data.get("last_activity", ""),
                word_count=word_count,
                sections_count=sections_count,
                status=status
            ))
        
        return proposals
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=ProposalDetail)
async def get_proposal(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    try:
        session_data = session_manager.get_session(session_id)
        
        if not session_data.get("current_content") and not session_data.get("plan"):
            raise HTTPException(status_code=404, detail="No proposal found in this session")
        
        # Extract title from plan
        plan = session_data.get("plan", "")
        title = "Untitled Proposal"
        if plan:
            lines = plan.split('\n')
            for line in lines:
                if line.strip().startswith('#'):
                    title = line.strip('#').strip()
                    break
        
        return ProposalDetail(
            session_id=session_id,
            title=title,
            plan=plan,
            content=session_data.get("current_content", ""),
            created_at=session_data.get("created_at", ""),
            updated_at=session_data.get("last_activity", ""),
            metadata=session_data.get("metadata", {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{session_id}/content")
async def update_proposal_content(
    session_id: str,
    content: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    try:
        session_data = session_manager.get_session(session_id)
        session_data["current_content"] = content
        session_data["last_activity"] = session_manager._get_timestamp()
        
        session_manager.update_session(session_id, session_data)
        
        return {
            "message": "Proposal content updated successfully",
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/export/{format}")
async def export_proposal(
    session_id: str,
    format: str,  # "md", "docx", "pdf"
    session_manager: SessionManager = Depends(get_session_manager)
):
    try:
        session_data = session_manager.get_session(session_id)
        content = session_data.get("current_content", "")
        
        if not content:
            raise HTTPException(status_code=404, detail="No proposal content to export")
        
        if format == "md":
            return {
                "format": "markdown",
                "content": content,
                "filename": f"proposal_{session_id}.md"
            }
        elif format == "docx":
            # TODO: Implement DOCX export
            raise HTTPException(status_code=501, detail="DOCX export not yet implemented")
        elif format == "pdf":
            # TODO: Implement PDF export
            raise HTTPException(status_code=501, detail="PDF export not yet implemented")
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))