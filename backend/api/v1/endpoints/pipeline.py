"""
Pipeline API endpoints for A-E workflow execution
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio
import json
from datetime import datetime

router = APIRouter()

class ExecuteStepRequest(BaseModel):
    step_id: str
    agent: str
    session_id: Optional[str] = None

class ExecuteStepResponse(BaseModel):
    success: bool
    message: str
    output_file: Optional[str] = None
    execution_time: float

# Mock 智能体映射
AGENT_MAPPING = {
    "DocumentParserAgent": "文档解析智能体",
    "StructureExtractor": "结构抽取智能体",
    "SpecExtractor": "规格提取智能体", 
    "PlanOutliner": "方案提纲智能体",
    "BidAssembler": "草案拼装智能体",
    "SanityChecker": "完整性校验智能体"
}

@router.post("/execute-step", response_model=ExecuteStepResponse)
async def execute_pipeline_step(request: ExecuteStepRequest):
    """
    执行pipeline中的单个步骤
    """
    try:
        start_time = datetime.now()
        
        # 模拟执行时间
        await asyncio.sleep(2)
        
        # 根据步骤ID生成对应的输出文件
        output_files = {
            "document_parsing": "招标文件.md",
            "structure_extraction": "投标文件_骨架.md",
            "spec_extraction": "技术规格书_提取.md", 
            "plan_outlining": "方案_提纲.md",
            "bid_assembly": "投标文件_草案.md",
            "sanity_check": "合规性报告.json"
        }
        
        output_file = output_files.get(request.step_id)
        
        # 计算执行时间
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return ExecuteStepResponse(
            success=True,
            message=f"成功执行 {AGENT_MAPPING.get(request.agent, request.agent)}",
            output_file=output_file,
            execution_time=execution_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"执行步骤失败: {str(e)}"
        )

@router.post("/execute-all")
async def execute_all_steps(background_tasks: BackgroundTasks, session_id: Optional[str] = None):
    """
    执行完整的A-E工作流pipeline
    """
    try:
        # 定义所有步骤（包括文档解析）
        steps = [
            {"id": "document_parsing", "agent": "DocumentParserAgent"},
            {"id": "structure_extraction", "agent": "StructureExtractor"},
            {"id": "spec_extraction", "agent": "SpecExtractor"},
            {"id": "plan_outlining", "agent": "PlanOutliner"}, 
            {"id": "bid_assembly", "agent": "BidAssembler"},
            {"id": "sanity_check", "agent": "SanityChecker"}
        ]
        
        results = []
        
        for step in steps:
            request = ExecuteStepRequest(
                step_id=step["id"],
                agent=step["agent"],
                session_id=session_id
            )
            result = await execute_pipeline_step(request)
            results.append({
                "step_id": step["id"],
                "agent": step["agent"],
                "result": result
            })
        
        return {
            "success": True,
            "message": "完整pipeline执行成功",
            "results": results,
            "total_steps": len(steps),
            "completed_steps": len([r for r in results if r["result"].success])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline执行失败: {str(e)}"
        )

@router.get("/status/{session_id}")
async def get_pipeline_status(session_id: str):
    """
    获取pipeline执行状态
    """
    try:
        # 这里应该从数据库或缓存中获取实际状态
        # 现在返回模拟数据
        return {
            "session_id": session_id,
            "status": "running",
            "current_step": "structure_extraction",
            "progress": 0.2,
            "completed_steps": [],
            "pending_steps": [
                "structure_extraction",
                "spec_extraction", 
                "plan_outlining",
                "bid_assembly",
                "sanity_check"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取状态失败: {str(e)}"
        )