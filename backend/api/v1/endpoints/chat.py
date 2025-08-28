from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional, AsyncGenerator
from pydantic import BaseModel
import json
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from workflow.graph import ProposalWorkflow
from workflow.state import WorkflowState
from services.session_manager import SessionManager, get_session_manager
import uuid

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    metadata: Dict[str, Any] = {}


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    selected_text: Optional[str] = None
    surrounding_context: Optional[str] = None
    optimization_goal: Optional[str] = None
    uploaded_files: List[Dict[str, Any]] = []


class ChatResponse(BaseModel):
    session_id: str
    message: str
    metadata: Dict[str, Any] = {}
    files_created: List[Dict[str, str]] = []
    conversation_history: List[ChatMessage] = []


async def stream_chat_response(
    request: ChatRequest,
    session_manager: SessionManager
) -> AsyncGenerator[str, None]:
    """Stream chat response using Server-Sent Events"""
    try:
        logger.info(f"Starting stream_chat_response for message: {request.message}")
        
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        session = session_manager.get_session(session_id)
        
        logger.info(f"Using session_id: {session_id}")
        
        # Send initial session info
        session_data = {'type': 'session', 'session_id': session_id}
        yield f"data: {json.dumps(session_data, ensure_ascii=False)}\n\n"
        logger.debug(f"Sent session data: {session_data}")
        
        # Initialize workflow
        workflow = ProposalWorkflow()
        
        # Send agent status update
        status_data = {'type': 'agent_status', 'agent': 'coordinator', 'action': 'analyzing_request'}
        yield f"data: {json.dumps(status_data, ensure_ascii=False)}\n\n"
        logger.debug(f"Sent agent status: {status_data}")
        
        # 不再发送旧的 PROPOSAL_PLAN.md 初始文件
        
        # Prepare state
        state: WorkflowState = {
            "user_input": request.message,
            "uploaded_files": request.uploaded_files,
            "file_summaries": [],
            "research_results": session.get("research_results", []),
            "plan": session.get("plan"),
            "plan_confirmed": session.get("plan_confirmed", False),
            "current_content": session.get("current_content"),
            "selected_text": request.selected_text,
            "surrounding_context": request.surrounding_context,
            "optimization_goal": request.optimization_goal,
            "conversation_history": session.get("conversation_history", []),
            "session_id": session_id,
            "current_action": "",
            "current_stage": "initial",
            "files_to_create": [],
            "metadata": {}
        }
        
        # Add user message to conversation
        state["conversation_history"].append({
            "role": "user",
            "content": request.message,
            "metadata": {},
            "timestamp": workflow._get_timestamp()
        })
        
        # Stream workflow execution - let the Coordinator determine the actual pipeline
        logger.info("Starting dynamic agent coordination...")
        
        # Brief delay to show initial analysis
        await asyncio.sleep(0.1)
        
        # Run workflow
        logger.info("Starting workflow execution")
        # Log file info without full content to avoid log pollution
        uploaded_files_info = []
        for file_info in state.get('uploaded_files', []):
            file_summary = {
                'name': file_info.get('name', 'unknown'),
                'type': file_info.get('type', 'unknown'),
                'content_length': len(file_info.get('content', '')) if file_info.get('content') else 0
            }
            uploaded_files_info.append(file_summary)
        logger.info(f"State uploaded_files: {uploaded_files_info}")
        result_state = await workflow.run(state)
        logger.info(f"Workflow completed. Current agent: {result_state.get('current_agent')}, Stage: {result_state.get('current_stage')}")
        logger.debug(f"Full workflow state keys: {list(result_state.keys())}")
        
        # Check if workflow is waiting for plan confirmation
        user_input_lower = request.message.lower()
        if ("开始执行" in user_input_lower or "start" in user_input_lower) and state.get("plan"):
            logger.info("User confirmed plan, continuing with writing")
            # Update state to confirm plan and continue
            result_state["plan_confirmed"] = True
            result_state["user_input"] = request.message
            
            # Run workflow again to continue with writing
            continue_state = await workflow.run(result_state)
            result_state = continue_state
        
        # Send completion status based on actual workflow stage
        current_agent = result_state.get("current_agent", "coordinator")
        current_stage = result_state.get("current_stage", "completed")
        
        # Map failed stages
        failed_stages = {"parsing_failed", "extraction_failed", "generation_failed"}
        if current_stage in failed_stages:
            completion_status = {'type': 'agent_status', 'agent': current_agent, 'action': current_stage, 'status': 'failed'}
        elif current_stage == "awaiting_plan_confirmation":
            completion_status = {'type': 'agent_status', 'agent': current_agent, 'action': 'awaiting_plan_confirmation', 'status': 'processing'}
        elif current_stage in {"project_completed", "generation_completed", "completed"}:
            completion_status = {'type': 'agent_status', 'agent': 'completed', 'action': 'finished', 'status': 'success'}
        elif current_stage == "writing_completed":
            completion_status = {'type': 'agent_status', 'agent': 'writer', 'action': 'writing_completed', 'status': 'success'}
        elif current_stage == "plan_created":
            completion_status = {'type': 'agent_status', 'agent': 'planner', 'action': 'plan_created', 'status': 'success'}
        elif current_stage == "research_completed":
            completion_status = {'type': 'agent_status', 'agent': 'researcher', 'action': 'research_completed', 'status': 'success'}
        else:
            completion_status = {'type': 'agent_status', 'agent': current_agent, 'action': current_stage, 'status': 'processing'}
            
        yield f"data: {json.dumps(completion_status, ensure_ascii=False)}\n\n"
        logger.debug(f"Sent completion status: {completion_status}")
        
        # Update session with created files
        session_update = dict(result_state)
        
        # Store created files in session for easy access
        files_created = result_state.get("files_to_create", [])
        if files_created:
            # Store files data in session
            session_files = {}
            for file in files_created:
                # 确定文件类型
                file_type = file.get("type", "other")
                if file["name"].endswith('.md'):
                    if 'PLAN' in file["name"].upper():
                        file_type = "plan"
                    elif 'PROPOSAL' in file["name"].upper():
                        file_type = "proposal"
                    else:
                        file_type = "wiki"
                
                session_files[file["name"]] = {
                    "content": file["content"],
                    "type": file_type
                }
            session_update["created_files"] = session_files
        
        # Store uploaded files in session for persistence
        uploaded_files = result_state.get("uploaded_files", [])
        if uploaded_files:
            session_update["uploaded_files"] = uploaded_files
            
        session_manager.update_session(session_id, session_update)
        
        # Extract response
        last_assistant_message = None
        for msg in reversed(result_state["conversation_history"]):
            if msg["role"] == "assistant":
                last_assistant_message = msg
                break
        
        response_content = last_assistant_message["content"] if last_assistant_message else "I'm processing your request..."
        
        # Stream the final response
        files_created = result_state.get("files_to_create", [])
        logger.info(f"Files created: {[f.get('name') for f in files_created]}")
        
        # Extract agent information from the last assistant message metadata
        response_metadata = result_state.get("metadata", {})
        if last_assistant_message and last_assistant_message.get("metadata"):
            response_metadata.update(last_assistant_message["metadata"])
        
        # Ensure current_agent is set in metadata
        if "current_agent" not in response_metadata:
            response_metadata["current_agent"] = result_state.get("current_agent", "coordinator")
        
        response_data = {
            'type': 'message',
            'session_id': session_id,
            'message': response_content,
            'metadata': response_metadata,
            'files_created': [
                {"name": f["name"], "content": f["content"]} 
                for f in files_created
            ]
        }
        
        logger.info(f"Sending response data with {len(files_created)} files")
        yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"
        logger.info("Stream completed successfully")
        
    except Exception as e:
        logger.error(f"Error in stream_chat_response: {str(e)}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"


@router.post("/message")
async def send_message_stream(
    request: ChatRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Stream chat messages using Server-Sent Events"""
    return StreamingResponse(
        stream_chat_response(request, session_manager),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@router.post("/message/sync", response_model=ChatResponse)
async def send_message_sync(
    request: ChatRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Synchronous chat endpoint for compatibility"""
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        session = session_manager.get_session(session_id)
        
        # Initialize workflow
        workflow = ProposalWorkflow()
        
        # Prepare state
        state: WorkflowState = {
            "user_input": request.message,
            "uploaded_files": request.uploaded_files,
            "file_summaries": [],
            "research_results": session.get("research_results", []),
            "plan": session.get("plan"),
            "plan_confirmed": session.get("plan_confirmed", False),
            "current_content": session.get("current_content"),
            "selected_text": request.selected_text,
            "surrounding_context": request.surrounding_context,
            "optimization_goal": request.optimization_goal,
            "conversation_history": session.get("conversation_history", []),
            "session_id": session_id,
            "current_action": "",
            "current_stage": "initial",
            "files_to_create": [],
            "metadata": {}
        }
        
        # Add user message to conversation
        state["conversation_history"].append({
            "role": "user",
            "content": request.message,
            "metadata": {},
            "timestamp": workflow._get_timestamp()
        })
        
        # Run workflow
        result_state = await workflow.run(state)
        
        # Update session with created files
        session_update = dict(result_state)
        
        # Store created files in session for easy access
        files_created = result_state.get("files_to_create", [])
        if files_created:
            # Store files data in session
            session_files = {}
            for file in files_created:
                session_files[file["name"]] = {
                    "content": file["content"],
                    "type": file.get("type", "other")
                }
            session_update["created_files"] = session_files
        
        # Store uploaded files in session for persistence
        uploaded_files = result_state.get("uploaded_files", [])
        if uploaded_files:
            session_update["uploaded_files"] = uploaded_files
            
        session_manager.update_session(session_id, session_update)
        
        # Extract response
        last_assistant_message = None
        for msg in reversed(result_state["conversation_history"]):
            if msg["role"] == "assistant":
                last_assistant_message = msg
                break
        
        response_content = last_assistant_message["content"] if last_assistant_message else "I'm processing your request..."
        
        # Convert conversation history
        conversation = [
            ChatMessage(
                role=msg["role"],
                content=msg["content"], 
                metadata=msg.get("metadata", {})
            )
            for msg in result_state["conversation_history"]
        ]
        
        # Extract agent information from the last assistant message metadata
        response_metadata = result_state.get("metadata", {})
        if last_assistant_message and last_assistant_message.get("metadata"):
            response_metadata.update(last_assistant_message["metadata"])
        
        # Ensure current_agent is set in metadata
        if "current_agent" not in response_metadata:
            response_metadata["current_agent"] = result_state.get("current_agent", "coordinator")
        
        return ChatResponse(
            session_id=session_id,
            message=response_content,
            metadata=response_metadata,
            files_created=[
                {"name": f["name"], "content": f["content"]} 
                for f in result_state.get("files_to_create", [])
            ],
            conversation_history=conversation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize", response_model=ChatResponse)
async def optimize_text(
    request: ChatRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    if not request.selected_text:
        raise HTTPException(status_code=400, detail="No text selected for optimization")
    
    try:
        session_id = request.session_id or str(uuid.uuid4())
        session = session_manager.get_session(session_id)
        
        workflow = ProposalWorkflow()
        
        # Prepare optimization state
        state: WorkflowState = {
            "user_input": request.message,
            "uploaded_files": [],
            "file_summaries": [],
            "research_results": [],
            "plan": session.get("plan"),
            "plan_confirmed": True,
            "current_content": session.get("current_content"),
            "selected_text": request.selected_text,
            "surrounding_context": request.surrounding_context,
            "optimization_goal": request.optimization_goal,
            "conversation_history": session.get("conversation_history", []),
            "session_id": session_id,
            "current_action": "optimize",
            "current_stage": "optimization_requested",
            "current_agent": "optimizer",
            "files_to_create": [],
            "metadata": {}
        }
        
        # Run optimization through coordinator
        result_state = await workflow.run(state)
        
        # Update session with optimized content if it's a plan optimization
        session_update = dict(result_state)
        
        # If this is a plan optimization, update the plan content
        optimized_content = result_state.get("optimized_content", "")
        if not optimized_content:
            # Try to extract from the last assistant message
            for msg in reversed(result_state["conversation_history"]):
                if msg["role"] == "assistant" and msg.get("metadata", {}).get("optimization_type"):
                    optimized_content = msg["content"]
                    break
        
        # If still not found, use the last assistant message content
        if not optimized_content:
            for msg in reversed(result_state["conversation_history"]):
                if msg["role"] == "assistant":
                    optimized_content = msg["content"]
                    break
        
        # Update the session plan if this was a plan optimization
        if optimized_content and result_state.get("current_action") == "optimize":
            logger.info(f"Updating session plan with optimized content, length: {len(optimized_content)}")
            session_update["plan"] = optimized_content
        else:
            logger.info(f"Not updating session plan. optimized_content: {bool(optimized_content)}, current_action: {result_state.get('current_action')}")
        
        session_manager.update_session(session_id, session_update)
        
        return ChatResponse(
            session_id=session_id,
            message=f"文本优化完成。",
            metadata={"optimized_content": optimized_content},
            files_created=[],
            conversation_history=[
                ChatMessage(
                    role=msg["role"],
                    content=msg["content"],
                    metadata=msg.get("metadata", {})
                )
                for msg in result_state["conversation_history"]
            ]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))