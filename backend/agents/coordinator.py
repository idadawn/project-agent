from typing import Dict, Any, List, Optional
import json
import asyncio
from .base import BaseAgent, AgentContext, AgentResponse
from workflow.bid_build_graph import run_build
# Import agents dynamically to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .document_parser import DocumentParserAgent
    from .key_extraction import KeyExtractionAgent
    from .bid_generator import BidGeneratorAgent


class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("coordinator")
        # Initialize agents lazily to avoid circular imports
        self._document_parser = None
        self._key_extraction = None
        self._bid_generator = None
        self._bid_format = None
        self.session_state = {}
    
    @property
    def document_parser(self):
        if self._document_parser is None:
            from .document_parser import DocumentParserAgent
            self._document_parser = DocumentParserAgent()
        return self._document_parser
    
    @property
    def key_extraction(self):
        if self._key_extraction is None:
            from .key_extraction import KeyExtractionAgent
            self._key_extraction = KeyExtractionAgent()
        return self._key_extraction
    
    @property
    def bid_generator(self):
        if self._bid_generator is None:
            from .bid_generator import BidGeneratorAgent
            self._bid_generator = BidGeneratorAgent()
        return self._bid_generator

    @property
    def bid_format(self):
        if self._bid_format is None:
            from .bid_format_agent import BidFormatAgent
            self._bid_format = BidFormatAgent()
        return self._bid_format
    
    def get_system_prompt(self) -> str:
        return """您是协调智能体 (Coordinator Agent)，招标文件处理系统的总指挥和唯一用户接口。

📋 **核心职责**：
1. **会话管理**: 与用户进行自然语言对话，协调整个招标文件处理流程
2. **意图识别与任务分派**: 分析用户需求，判断是否需要处理招标文件
3. **工作流协调**: 管理从文档上传到投标方案生成的完整流程
4. **状态管理**: 维护文件处理状态，更新项目进度
5. **用户交互**: 引导用户确认流程节点，收集反馈和修改意见

🤖 **专业智能体团队**：
- 📄 **Document Parser**: 文档解析，识别招标文件结构
- 🔍 **Key Extraction**: 关键信息提取，识别技术规格书和投标格式要求
- 📝 **Bid Generator**: 投标文件生成，创建完整的投标方案

💼 **处理流程**：
1. 文档上传 → 保存到上传文件文件夹
2. 文档解析 → 结构化解析，保存到解析文件文件夹
3. 信息提取 → 提取技术规格书和投标格式要求
4. 方案生成 → 生成投标方案文件

📊 **状态管理**：使用 ✅已完成、🚧进行中、⏳待处理 来标记任务状态

🎯 **目标**: 帮助用户高效处理招标文件，生成专业的投标方案。"""
    
    async def execute(self, context: AgentContext) -> AgentResponse:
        try:
            # 分析用户请求，判断是否需要处理招标文件
            analysis = await self._analyze_user_request(context)
            
            session_state = context.project_state or {}
            current_stage = session_state.get("current_stage", "initial")
            
            # 根据当前阶段决定下一步行动
            if current_stage == "initial":
                return await self._handle_initial_request(context)
            elif current_stage == "parsing_requested":
                # 处理自动触发的解析请求
                return await self._handle_parsing_requested(context)
            elif current_stage == "document_parsing":
                return await self._coordinate_document_parsing(context)
            elif current_stage == "parsing_completed":
                # 解析完成后，收到用户指令时继续到关键信息提取
                return await self._coordinate_key_extraction(context)
            elif current_stage == "bid_format_completed":
                # 投标文件格式已生成 → 进入关键信息提取
                return await self._coordinate_key_extraction(context)
            elif current_stage == "bid_format_analysis":
                return await self._coordinate_bid_format(context)
            elif current_stage == "key_extraction":
                return await self._coordinate_key_extraction(context)
            elif current_stage == "extraction_completed":
                # 提取完成后，收到用户指令时继续到投标文件生成
                return await self._coordinate_bid_generation(context)
            elif current_stage == "bid_generation":
                return await self._coordinate_bid_generation(context)
            elif current_stage == "awaiting_confirmation":
                return await self._handle_confirmation(context)
            else:
                return await self._handle_general_coordination(context)
                
        except Exception as e:
            return AgentResponse(
                content=f"协调过程中发生错误: {str(e)}",
                status="error"
            )
    
    async def _analyze_user_request(self, context: AgentContext) -> dict:
        """分析用户请求，判断是否需要处理招标文件"""
        user_input = context.user_input.lower()
        
        # 检查是否有上传文件
        has_uploaded_files = bool(context.uploaded_files)
        
        # 检查用户输入是否包含招标相关关键词
        bidding_keywords = ['招标', '投标', '标书', '技术规格', '投标文件', '第四章', '第五章', '技术方案']
        has_bidding_intent = any(keyword in user_input for keyword in bidding_keywords)
        
        # 决策逻辑
        if has_uploaded_files and has_bidding_intent:
            return {"action": "process_bidding_documents", "next_stage": "document_parsing"}
        elif has_uploaded_files:
            return {"action": "process_documents", "next_stage": "document_parsing"}
        elif has_bidding_intent:
            return {"action": "discuss_bidding", "next_stage": "general"}
        else:
            return {"action": "general_conversation", "next_stage": "general"}
    
    async def _handle_parsing_requested(self, context: AgentContext) -> AgentResponse:
        """处理自动触发的解析请求"""
        # 自动触发解析请求，直接进入文档解析阶段
        context.project_state = context.project_state or {}
        context.project_state["current_stage"] = "document_parsing"
        
        return AgentResponse(
            content="🤝 **Coordinator 智能体**: 检测到文件上传，自动启动文档解析流程。\n\n📋 **处理流程**:\n1. 📄 文档解析 → 2. 🔍 关键信息提取 → 3. 📝 投标方案生成\n\n🚀 正在启动文档解析阶段...",
            metadata={
                "current_agent": "coordinator",
                "stage": "document_parsing",
                "action": "auto_started_bidding_processing"
            },
            next_actions=["proceed_to_parsing"]
        )

    async def _handle_initial_request(self, context: AgentContext) -> AgentResponse:
        """处理初始请求"""
        analysis = await self._analyze_user_request(context)
        
        if analysis["action"] == "process_bidding_documents":
            # 开始招标文件处理流程
            context.project_state = context.project_state or {}
            context.project_state["current_stage"] = "document_parsing"
            
            return AgentResponse(
                content="🤝 **Coordinator 智能体**: 检测到招标文件上传，开始处理流程。\n\n📋 **处理流程**:\n1. 📄 文档解析 → 2. 🔍 关键信息提取 → 3. 📝 投标方案生成\n\n🚀 正在启动文档解析阶段...",
                metadata={
                    "current_agent": "coordinator",
                    "stage": "document_parsing",
                    "action": "starting_bidding_processing"
                },
                next_actions=["proceed_to_parsing"]
            )
        else:
            # 一般对话处理
            return await self._handle_general_coordination(context)
    
    async def _coordinate_document_parsing(self, context: AgentContext) -> AgentResponse:
        """协调文档解析阶段"""
        context.project_state = context.project_state or {}
        context.project_state["current_stage"] = "document_parsing"
        context.project_state["current_agent"] = "document_parser"
        
        # 调用文档解析智能体
        parse_response = await self.document_parser.execute(context)
        
        # 更新状态
        context.project_state["parsed_documents"] = parse_response.metadata.get("parsed_documents", [])
        
        # 失败分支：不要推进到下一阶段
        if parse_response.status != "completed":
            context.project_state["current_stage"] = "parsing_failed"
            return AgentResponse(
                content=f"❌ 文档解析失败\n\n{parse_response.content}",
                metadata={
                    "current_agent": "coordinator",
                    "stage": "parsing_failed",
                    "error": parse_response.metadata.get("error"),
                },
                status="failed",
                next_actions=[]
            )

        # 成功分支：按照需求停止在解析完成，不继续后续阶段
        context.project_state["current_stage"] = "parsing_completed"
        return AgentResponse(
            content=f"✅ **Document Parser 智能体** 已完成文档转换与解析\n\n{parse_response.content}\n\n（当前按要求仅完成Word→Markdown并保存至解析文件夹，不继续后续步骤。）",
            metadata={
                "current_agent": "coordinator",
                "stage": "parsing_completed",
                "parsed_documents": parse_response.metadata.get("parsed_documents", []),
                # 透传已创建文件，前端可立即展示
                "files_to_create": parse_response.metadata.get("files_to_create", [])
            },
            next_actions=[]
        )
    
    async def _coordinate_key_extraction(self, context: AgentContext) -> AgentResponse:
        """协调关键信息提取阶段"""
        context.project_state = context.project_state or {}
        context.project_state["current_stage"] = "key_extraction"
        context.project_state["current_agent"] = "key_extraction"
        
        # 调用关键信息提取智能体
        extraction_response = await self.key_extraction.execute(context)
        
        # 更新状态
        context.project_state["extracted_info"] = extraction_response.metadata.get("extracted_info", {})
        
        # 失败分支：不要推进到生成阶段
        if extraction_response.status != "completed":
            context.project_state["current_stage"] = "extraction_failed"
            return AgentResponse(
                content=f"❌ 关键信息提取失败\n\n{extraction_response.content}",
                metadata={
                    "current_agent": "coordinator",
                    "stage": "extraction_failed",
                    "error": extraction_response.metadata.get("error"),
                },
                status="failed",
                next_actions=[]
            )

        # 成功分支：停在提取完成，等待用户确认是否生成
        context.project_state["current_stage"] = "extraction_completed"
        return AgentResponse(
            content=f"✅ **Key Extraction 智能体** 已完成关键信息提取\n\n{extraction_response.content}\n\n是否继续生成‘投标文件.md’？回复‘继续执行’进入方案生成。",
            metadata={
                "current_agent": "coordinator",
                "stage": "extraction_completed",
                "extracted_info": extraction_response.metadata.get("extracted_info", {})
            },
            next_actions=[]
        )
    
    async def _coordinate_bid_generation(self, context: AgentContext) -> AgentResponse:
        """协调投标文件生成阶段"""
        context.project_state = context.project_state or {}
        context.project_state["current_stage"] = "bid_generation"
        context.project_state["current_agent"] = "bid_generator"
        
        # 调用投标文件生成智能体
        generation_response = await self.bid_generator.execute(context)
        
        # 更新状态
        context.project_state["generated_bid"] = generation_response.metadata.get("generated_bid", {})
        
        # 失败分支：不要标记为完成，也不推进
        if generation_response.status != "completed":
            context.project_state["current_stage"] = "generation_failed"
            return AgentResponse(
                content=f"❌ **Bid Generator 智能体** 生成失败\n\n{generation_response.content}",
                metadata={
                    "current_agent": "coordinator",
                    "stage": "generation_failed",
                    **generation_response.metadata,
                },
                status="failed",
                next_actions=[]
            )

        # 成功分支：标记完成
        context.project_state["current_stage"] = "completed"
        return AgentResponse(
            content=f"✅ **Bid Generator 智能体** 已完成投标方案生成\n\n{generation_response.content}",
            metadata={
                "current_agent": "coordinator",
                "next_stage": "completed",
                "stage": "generation_completed",
                "generated_bid": generation_response.metadata.get("generated_bid", {}),
                "files_to_create": generation_response.metadata.get("files_to_create", [])
            },
            next_actions=["process_completed"]
        )
    
    async def _handle_confirmation(self, context: AgentContext) -> AgentResponse:
        """处理用户确认请求"""
        user_input = context.user_input.lower()
        
        if "确认" in user_input or "开始" in user_input or "执行" in user_input:
            # 用户确认执行
            context.project_state["confirmed"] = True
            next_stage = context.project_state.get("next_stage_after_confirmation", "document_parsing")
            context.project_state["current_stage"] = next_stage
            
            return AgentResponse(
                content="✅ 用户确认执行，继续处理流程。",
                metadata={
                    "current_agent": "coordinator",
                    "next_stage": next_stage,
                    "stage": "confirmation_received"
                },
                next_actions=[f"proceed_to_{next_stage}"]
            )
        else:
            # 用户需要更多信息或修改
            return AgentResponse(
                content="请确认是否开始处理招标文件？回复'确认'开始执行，或提出您的修改要求。",
                metadata={
                    "current_agent": "coordinator",
                    "stage": "awaiting_confirmation"
                },
                next_actions=["await_user_confirmation"]
            )
    
    async def _handle_general_coordination(self, context: AgentContext) -> AgentResponse:
        """处理一般性协调请求"""
        user_text = (context.user_input or "").strip()
        # 触发词：继续执行/开始/执行/生成模板 → 直接推进到关键信息提取
        trigger_keywords = ["继续", "继续执行", "开始", "执行", "生成模板"]
        if any(k in user_text for k in trigger_keywords):
            return await self._coordinate_bid_build(context)

        return AgentResponse(
            content="🤝 **Coordinator 智能体**: 我来协助您处理招标文件相关事务。\n\n请上传招标文件或告诉我您的具体需求，我会协调专业团队为您处理。",
            metadata={
                "current_agent": "coordinator",
                "stage": "general_coordination"
            },
            next_actions=["await_user_input"]
        )

    async def _coordinate_bid_format(self, context: AgentContext) -> AgentResponse:
        """协调‘投标文件格式’分析与框架生成"""
        context.project_state = context.project_state or {}
        context.project_state["current_stage"] = "bid_format_analysis"
        context.project_state["current_agent"] = "bid_format"

        result = await self.bid_format.execute(context)

        if result.status != "completed":
            context.project_state["current_stage"] = "bid_format_failed"
            return AgentResponse(
                content=f"❌ 投标文件格式分析失败\n\n{result.content}",
                metadata={
                    "current_agent": "coordinator",
                    "stage": "bid_format_failed",
                    "error": result.metadata.get("error") if result.metadata else None,
                },
                status="failed",
                next_actions=[]
            )

        # 成功后，停在 bid_format_completed（等你确认或继续）
        context.project_state["current_stage"] = "bid_format_completed"
        return AgentResponse(
            content="✅ 已生成投标文件框架（投标文件/投标文件.md）。是否继续进行关键信息提取和方案生成？",
            metadata={
                "current_agent": "coordinator",
                "stage": "bid_format_completed",
                "files_to_create": result.metadata.get("files_to_create", []) if result.metadata else [],
            },
            next_actions=[]
        )

    async def _coordinate_bid_build(self, context: AgentContext) -> AgentResponse:
        """协调最小落地版 A–E 工作流（结构→规格→提纲→拼装→校验）"""
        context.project_state = context.project_state or {}
        # 优先使用文档解析产出的标准路径；若不存在，则依然允许A–E以兜底模板运行
        tender_path = "/root/project/git/project-agent/wiki/招标文件.md"
        wiki_dir = "wiki"
        meta = context.project_state.get("meta", {}) if isinstance(context.project_state, dict) else {}

        try:
            result = run_build(session_id=context.project_state.get("session_id", "coordinator-session"), tender_path=tender_path, wiki_dir=wiki_dir, meta=meta)
            # 写回关键路径到状态
            context.project_state.update({
                "outline_path": result.get("outline_path"),
                "spec_path": result.get("spec_path"),
                "plan_path": result.get("plan_path"),
                "plan_draft_path": result.get("plan_draft_path"),
                "draft_path": result.get("draft_path"),
                "sanity_report_path": result.get("sanity_report_path"),
                "current_stage": "bid_build_completed",
            })

            # 生成用户提示
            created = [
                ("投标文件_骨架.md", result.get("outline_path")),
                ("技术规格书_提取.md", result.get("spec_path")),
                ("方案_提纲.md", result.get("plan_path")),
                ("方案_草稿.md", result.get("plan_draft_path")),
                ("投标文件_草案.md", result.get("draft_path")),
                ("sanity_report.json", result.get("sanity_report_path")),
            ]
            lines = [f"- {name}: {path}" for name, path in created if path]
            msg = "\n".join(["✅ 已完成最小链路（A–E）生成以下文件:"] + lines)

            return AgentResponse(
                content=msg,
                metadata={
                    "current_agent": "coordinator",
                    "stage": "bid_build_completed",
                    "files_to_create": [],
                },
                next_actions=[],
            )
        except Exception as e:
            context.project_state["current_stage"] = "bid_build_failed"
            return AgentResponse(
                content=f"❌ A–E 工作流执行失败: {str(e)}",
                metadata={
                    "current_agent": "coordinator",
                    "stage": "bid_build_failed",
                },
                status="error",
                next_actions=[],
            )
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")