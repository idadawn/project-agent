from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app_core.llm_client import BaseLLMClient, llm_manager


class AgentContext(BaseModel):
    user_input: str
    uploaded_files: List[Dict[str, Any]] = []
    file_summaries: List[Dict[str, Any]] = []
    selected_text: Optional[str] = ""
    surrounding_context: Optional[str] = ""
    existing_content: Optional[str] = ""
    parsed_documents: List[Dict[str, Any]] = []
    extracted_info: Dict[str, Any] = {}
    project_state: Dict[str, Any] = {}
    task_type: str = "bid_processing"


class AgentResponse(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}
    next_actions: List[str] = []
    status: str = "completed"


class BaseAgent(ABC):
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.llm_client: BaseLLMClient = llm_manager.get_client(agent_name)
    
    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResponse:
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        pass
    
    async def _generate_response(
        self, 
        context: AgentContext, 
        additional_instructions: str = ""
    ) -> str:
        system_prompt = self.get_system_prompt()
        if additional_instructions:
            system_prompt += f"\n\nAdditional instructions: {additional_instructions}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self._format_user_message(context)}
        ]
        
        return await self.llm_client.generate(messages)
    
    def _format_user_message(self, context: AgentContext) -> str:
        message_parts = [f"User request: {context.user_input}"]
        
        if context.uploaded_files:
            message_parts.append("\nUploaded files:")
            for file_info in context.uploaded_files:
                message_parts.append(f"- {file_info.get('filename', 'Unknown')}: {file_info.get('file_type', '')}")
        
        if context.file_summaries:
            message_parts.append("\nFile summaries:")
            for summary in context.file_summaries:
                message_parts.append(f"- {summary.get('filename', 'Unknown')}: {summary.get('summary', '')[:100]}...")
        
        if context.selected_text:
            message_parts.append(f"\nSelected text: {context.selected_text[:200]}...")
        
        if context.surrounding_context:
            message_parts.append(f"\nSurrounding context: {context.surrounding_context[:200]}...")
        
        if context.existing_content:
            message_parts.append(f"\nExisting content: {context.existing_content[:200]}...")
        
        if context.parsed_documents:
            message_parts.append("\nParsed documents:")
            for doc in context.parsed_documents:
                message_parts.append(f"- {doc.get('filename', 'Unknown')}: {doc.get('structure_summary', '')}")
        
        if context.extracted_info:
            message_parts.append("\nExtracted information:")
            for key, value in context.extracted_info.items():
                message_parts.append(f"- {key}: {str(value)[:200]}...")
        
        return "\n".join(message_parts)