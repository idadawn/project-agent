from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from services.session_manager import SessionManager, get_session_manager
from workflow.state import ConversationSnapshot

router = APIRouter()


class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    last_activity: str
    message_count: int
    has_proposal: bool
    proposal_title: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    data: Dict[str, Any]
    snapshots: List[ConversationSnapshot] = []


@router.get("/list", response_model=List[SessionInfo])
async def list_sessions(
    session_manager: SessionManager = Depends(get_session_manager)
):
    try:
        sessions = session_manager.list_sessions()
        
        session_infos = []
        for session_id, session_data in sessions.items():
            conversation_history = session_data.get("conversation_history", [])
            proposal_title = None
            
            # Try to extract proposal title from plan
            plan = session_data.get("plan", "")
            if plan:
                lines = plan.split('\n')
                for line in lines:
                    if line.strip().startswith('#'):
                        proposal_title = line.strip('#').strip()
                        break
            
            session_infos.append(SessionInfo(
                session_id=session_id,
                created_at=session_data.get("created_at", ""),
                last_activity=session_data.get("last_activity", ""),
                message_count=len(conversation_history),
                has_proposal=bool(session_data.get("current_content")),
                proposal_title=proposal_title
            ))
        
        return session_infos
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    try:
        session_data = session_manager.get_session(session_id)
        snapshots = session_manager.get_snapshots(session_id)
        
        return SessionResponse(
            session_id=session_id,
            data=session_data,
            snapshots=snapshots
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/snapshot")
async def create_snapshot(
    session_id: str,
    description: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    try:
        snapshot = session_manager.create_snapshot(session_id, description)
        
        return {
            "message": "Snapshot created successfully",
            "snapshot_id": snapshot.timestamp,
            "description": snapshot.description
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/restore/{snapshot_id}")
async def restore_snapshot(
    session_id: str,
    snapshot_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    try:
        session_manager.restore_snapshot(session_id, snapshot_id)
        
        return {
            "message": "Session restored from snapshot successfully",
            "snapshot_id": snapshot_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    try:
        session_manager.delete_session(session_id)
        
        return {
            "message": "Session deleted successfully",
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/files")
async def get_session_files(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    try:
        session_data = session_manager.get_session(session_id)
        
        files = []
        
        # Get uploaded files first
        uploaded_files = session_data.get("uploaded_files", [])
        for uploaded_file in uploaded_files:
            files.append({
                "name": uploaded_file.get("name", "unknown"),
                "content": uploaded_file.get("content", ""),
                "type": "upload",  # Always set to 'upload' for uploaded files
                "folder": "uploads"
            })
        
        # Get files from created_files field (new storage method)
        created_files = session_data.get("created_files", {})
        for filename, file_data in created_files.items():
            # 确定文件类型
            file_type = file_data.get("type", "other")
            if filename.endswith('.md'):
                if 'PLAN' in filename.upper():
                    file_type = "plan"
                elif 'PROPOSAL' in filename.upper():
                    file_type = "proposal"
                else:
                    file_type = "wiki"
            
            files.append({
                "name": filename,
                "content": file_data["content"],
                "type": file_type,
                "folder": "root"
            })
        
        # 移除旧的 PROPOSAL_PLAN.md 兼容回退
        
        return {"files": files}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))