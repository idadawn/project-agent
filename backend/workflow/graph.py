from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from .state import WorkflowState
from agents.coordinator import CoordinatorAgent
from agents.base import AgentContext


class ProposalWorkflow:
    def __init__(self):
        self.coordinator = CoordinatorAgent()
        
        # 简化工作流 - 只保留一个coordinator节点作为智能体调度中心
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(WorkflowState)
        
        # 添加coordinator节点 - 它会动态调度其他智能体
        workflow.add_node("coordinator", self._coordinator_node)
        
        # 设置入口点
        workflow.set_entry_point("coordinator") 
        
        # 根据coordinator的响应决定是否继续
        workflow.add_conditional_edges(
            "coordinator",
            self._should_continue,
            {
                "continue": "coordinator",  # 继续执行coordinator
                "end": END  # 结束工作流
            }
        )
        
        return workflow.compile()
    
    def _should_continue(self, state: WorkflowState) -> str:
        """根据当前状态决定是否继续执行coordinator"""
        # 检查当前工作流状态
        current_stage = state.get("current_stage", "")
        uploaded_files = state.get("uploaded_files", [])
        
        # 安全检查：防止无限循环
        iteration_count = state.get("iteration_count", 0)
        if iteration_count > 30:  # 设置合理的最大迭代次数
            print(f"DEBUG _should_continue: Max iterations reached ({iteration_count}), ending workflow")
            return "end"
        
        # 增加迭代计数
        state["iteration_count"] = iteration_count + 1
        
        # 调试信息
        print(f"DEBUG _should_continue: current_stage = {current_stage}, iteration = {iteration_count + 1}")
        
        # 检查是否应该结束工作流（保留最终完成态；放宽解析/提取完成态以便收到"继续执行"后推进）
        if current_stage in ["completed", "generation_completed", "bid_build_completed", "bid_build_failed"]:
            print(f"DEBUG _should_continue: Ending workflow due to completed stage: {current_stage}")
            return "end"
        
        # 如果当前阶段是处理中阶段，继续执行
        if current_stage in [
            "document_parsing",
            "bid_format_analysis",
            "key_extraction",
            "bid_generation",
            "awaiting_confirmation",
            "parsing_completed",
            "extraction_completed",
            "bid_format_completed",
        ]:
            print(f"DEBUG _should_continue: Continuing due to active stage: {current_stage}")
            
            # 检查是否已经处理过这个阶段，防止无限循环
            if current_stage in ["document_parsing", "bid_format_analysis", "key_extraction", "bid_generation"]:
                stage_processed_key = f"{current_stage}_processed"
                if state.get(stage_processed_key):
                    print(f"DEBUG _should_continue: Stage {current_stage} already processed, ending")
                    return "end"
            
            return "continue"

        # 由协调节点设置的临时阶段：请求解析 → 仅推进一次
        if current_stage == "parsing_requested":
            # 检查是否已经处理过这个请求，防止无限循环
            if state.get("parsing_requested_processed"):
                print("DEBUG _should_continue: parsing_requested already processed, ending")
                return "end"
            print("DEBUG _should_continue: parsing_requested → continue once")
            # 标记为已处理，防止下次继续
            state["parsing_requested_processed"] = True
            return "continue"
        
        # 检查最后一条消息的metadata中的next_actions
        last_message = state.get("conversation_history", [])[-1] if state.get("conversation_history") else {}
        metadata = last_message.get("metadata", {})
        
        # 检查是否有next_actions指示需要继续
        next_actions = metadata.get("next_actions", [])
        
        # 只有当阶段不是完成状态时，才根据next_actions继续
        if next_actions and any(action in ["proceed_to_parsing", "proceed_to_extraction", "proceed_to_generation", "process_completed"] for action in next_actions):
            # 检查当前阶段是否已经是完成状态
            if current_stage in ["generation_completed", "completed"]:
                print(f"DEBUG _should_continue: Stage {current_stage} is completed, ignoring next_actions: {next_actions}")
                return "end"
            else:
                print(f"DEBUG _should_continue: Continuing due to next_actions: {next_actions}")
                return "continue"
        
        # 检查是否有next_stage指示需要继续
        next_stage = metadata.get("next_stage", "")
        if next_stage and next_stage not in ["completed", "general_coordination"]:
            # 检查当前阶段是否已经是完成状态
            if current_stage in ["parsing_completed", "extraction_completed", "generation_completed", "completed"]:
                print(f"DEBUG _should_continue: Stage {current_stage} is completed, ignoring next_stage: {next_stage}")
                return "end"
            
            # 检查关键信息是否完整，如果不完整则停止执行
            if next_stage == "bid_generation":
                extracted_info = state.get("extracted_info", {})
                if extracted_info:
                    missing_critical = self._check_missing_critical_info(extracted_info)
                    if missing_critical:
                        print(f"DEBUG _should_continue: Critical info missing, stopping: {missing_critical}")
                        return "end"
            
            print(f"DEBUG _should_continue: Continuing due to next_stage: {next_stage}")
            return "continue"
        
        # 默认情况下结束工作流
        print(f"DEBUG _should_continue: Ending workflow, stage: {current_stage}, next_stage: {next_stage}")
        return "end"
    
    async def _coordinator_node(self, state: WorkflowState) -> WorkflowState:
        """Coordinator节点 - 作为智能体调度中心"""
        context = self._create_context(state)
        uploaded_files = state.get('uploaded_files', [])
        uploaded_files_info = [
            {
                'name': f.get('name', 'unknown'), 
                'type': f.get('type', 'unknown'),
                'content_length': len(f.get('content', '')) if f.get('content') else 0
            } 
            for f in uploaded_files
        ]
        print(f"DEBUG: Workflow state uploaded_files: {uploaded_files_info}")
        
        context_files_info = [
            {
                'name': f.get('name', 'unknown'), 
                'type': f.get('type', 'unknown'),
                'content_length': len(f.get('content', '')) if f.get('content') else 0
            } 
            for f in context.uploaded_files
        ]
        print(f"DEBUG: Context uploaded_files: {context_files_info}")
        print(f"DEBUG: Current stage before coordinator: {state.get('current_stage', 'N/A')}")
        response = await self.coordinator.execute(context)
        
        # 确保响应metadata包含当前智能体信息
        response_metadata = response.metadata.copy()
        if "current_agent" not in response_metadata:
            response_metadata["current_agent"] = "coordinator"
        
        # 更新对话历史
        state["conversation_history"].append({
            "role": "assistant", 
            "content": response.content,
            "metadata": response_metadata,
            "timestamp": self._get_timestamp()
        })
        
        # 处理智能体创建的文件
        files_to_create = response.metadata.get("files_to_create", [])
        if files_to_create:
            if "files_to_create" not in state:
                state["files_to_create"] = []
            state["files_to_create"].extend(files_to_create)
        
        # 更新项目状态（从coordinator的元数据中获取）
        if "current_agent" in response.metadata:
            state["current_agent"] = response.metadata["current_agent"]
        if "stage" in response.metadata:
            state["current_stage"] = response.metadata["stage"]
            print(f"DEBUG: Updated current_stage from response metadata: {state['current_stage']}")
        
        # 同步context.project_state中的状态更新到workflow state（但不覆盖current_stage）
        if context.project_state:
            # 只在response.metadata没有stage时才同步current_stage，防止覆盖coordinator的正确状态
            if "stage" not in response.metadata and "current_stage" in context.project_state:
                state["current_stage"] = context.project_state["current_stage"]
                print(f"DEBUG: Synced current_stage from context: {state['current_stage']}")
            
            # 同步其他重要的状态信息
            for key in ["parsed_documents", "extracted_info", "generated_bid"]:
                if key in context.project_state:
                    state[key] = context.project_state[key]
        
        # 调试：检查响应metadata中的stage信息
        print(f"DEBUG: Response metadata stage: {response.metadata.get('stage', 'N/A')}")
        print(f"DEBUG: Response metadata next_stage: {response.metadata.get('next_stage', 'N/A')}")
        print(f"DEBUG: Response metadata next_actions: {response.metadata.get('next_actions', [])}")
            
        # 保留其他重要状态信息
        for key in ["plan", "research_results", "optimized_content"]:
            if key in response.metadata:
                state[key] = response.metadata[key]
        
        # 关键修复：如果DocumentParserAgent更新了tender_path，同步到state和project_state
        if "tender_path" in response.metadata:
            state["tender_path"] = response.metadata["tender_path"]
            if context.project_state:
                context.project_state["tender_path"] = response.metadata["tender_path"]
            print(f"DEBUG: Updated tender_path to: {response.metadata['tender_path']}")
        
        # 更新通用metadata
        state["metadata"].update(response.metadata)
        
        print(f"DEBUG: Current stage after coordinator: {state.get('current_stage', 'N/A')}")

        # 若存在上传文件且仍停在一般协调阶段，则设置一次性推进标记与过渡阶段，避免无限循环
        if uploaded_files and state.get("current_stage", "") in ["", "initial", "general_coordination"] and not state.get("parsing_auto_triggered"):
            state["parsing_auto_triggered"] = True
            state["current_stage"] = "parsing_requested"
            state["metadata"]["next_stage"] = "document_parsing"
            print("DEBUG: Auto-trigger parsing once due to uploaded files → set parsing_requested")
        
        # 防止重复处理同一阶段：如果当前阶段已经处理过，则结束工作流
        current_stage = state.get("current_stage", "")
        if current_stage in ["document_parsing", "key_extraction", "bid_generation"]:
            stage_processed_key = f"{current_stage}_processed"
            if state.get(stage_processed_key):
                print(f"DEBUG: Stage {current_stage} already processed, ending workflow")
                return state
            else:
                # 标记当前阶段为已处理
                state[stage_processed_key] = True
                print(f"DEBUG: Marked stage {current_stage} as processed")
        
        # 检查阶段是否应该结束：如果当前阶段是完成状态，则结束工作流
        if current_stage in ["parsing_completed", "extraction_completed", "generation_completed", "completed", "bid_build_completed", "bid_build_failed"]:
            print(f"DEBUG: Stage {current_stage} is completed, ending workflow")
            return state
        
        # 强制结束条件：如果已经处理过parsing_requested且当前阶段是document_parsing，则结束
        if state.get("parsing_auto_triggered") and current_stage == "document_parsing":
            print("DEBUG: Force ending workflow after parsing_requested → document_parsing transition")
            return state
        
        return state
    
    def _create_context(self, state: WorkflowState) -> AgentContext:
        """从状态创建智能体上下文"""
        return AgentContext(
            user_input=state["user_input"],
            uploaded_files=state.get("uploaded_files", []),
            file_summaries=state["file_summaries"],
            selected_text=state.get("selected_text") or "",
            surrounding_context=state.get("surrounding_context") or "",
            existing_content=state.get("current_content") or "",
            project_state=state
        )
    
    async def run(self, initial_state: WorkflowState) -> WorkflowState:
        """运行工作流"""
        print(f"DEBUG: Initial state stage: {initial_state.get('current_stage', 'N/A')}")
        # 设置递归限制配置，防止无限循环
        config = {"recursion_limit": 50}
        result = await self.graph.ainvoke(initial_state, config=config)
        print(f"DEBUG: Final state stage: {result.get('current_stage', 'N/A')}")
        return result
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _check_missing_critical_info(self, extracted_info: Dict[str, Any]) -> str:
        """检查关键信息是否完整"""
        missing_items = []
        
        for filename, file_info in extracted_info.items():
            tech_specs = file_info.get('tech_specifications', {})
            bid_format = file_info.get('bid_format', {})
            
            if not tech_specs.get('found'):
                missing_items.append(f"• {filename}: 技术规格书")
            if not bid_format.get('found'):
                missing_items.append(f"• {filename}: 投标文件格式")
        
        if missing_items:
            return "\n".join(missing_items)
        return ""