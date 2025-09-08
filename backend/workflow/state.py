from typing import Dict, Any, List, Optional, TypedDict
from pydantic import BaseModel


class WorkflowState(TypedDict):
    user_input: str
    uploaded_files: List[Dict[str, Any]]
    file_summaries: List[Dict[str, Any]]
    research_results: List[str]
    plan: Optional[str]
    plan_confirmed: bool
    current_content: Optional[str]
    selected_text: Optional[str]
    surrounding_context: Optional[str]
    optimization_goal: Optional[str]
    conversation_history: List[Dict[str, Any]]
    session_id: str
    current_action: str
    current_stage: str
    files_to_create: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class BidState(TypedDict, total=False):
    """投标文件构建状态"""
    session_id: str
    tender_path: str          # /uploads/招标文件.md
    bid_md_path: str          # /wiki/投标文件.md（你已有）
    outline_path: str         # /wiki/投标文件_骨架.md
    spec_path: str            # /wiki/技术规格书_提取.md
    wiki_dir: str             # 输出目录
    meta: Dict[str, Any]      # 项目名/编号/投标人等
    outline_sections: List[str]  # 提取的章节列表
    spec_extracted: bool      # 是否成功提取规格书
    # 用户确认状态
    outline_confirmed: bool   # 招标文件骨架是否确认
    spec_confirmed: bool      # 技术规格书是否确认
    current_step: str         # 当前步骤
    waiting_for_confirmation: bool  # 是否等待用户确认


class ProposalPlan(BaseModel):
    title: str
    sections: List[Dict[str, str]]  # {"title": "...", "description": "...", "status": "pending|in_progress|completed"}
    created_at: str
    updated_at: str


class ProposalContent(BaseModel):
    title: str
    content: str
    plan_id: str
    version: int
    created_at: str
    updated_at: str


class ConversationSnapshot(BaseModel):
    timestamp: str
    state: WorkflowState
    files: Dict[str, str]  # filename -> content
    description: str