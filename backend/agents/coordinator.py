from typing import Dict, Any, List, Optional
import json
import asyncio
from .base import BaseAgent, AgentContext, AgentResponse
from workflow.bid_build_graph import run_build
from agents.plan_outliner import PlanOutliner


class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("coordinator")
        self.session_state = {}
    
    def get_system_prompt(self) -> str:
        return """您是协调智能体 (Coordinator Agent)，招标文件处理系统的总指挥和唯一用户接口。

📋 **核心职责**：
1. **会话管理**: 与用户进行自然语言对话，协调整个招标文件处理流程
2. **意图识别与任务分派**: 分析用户需求，判断是否需要处理招标文件
3. **工作流协调**: 管理结构抽取与技术规格提取流程的执行
4. **状态管理**: 维护文件处理状态，更新项目进度
5. **用户交互**: 引导用户确认流程节点，收集反馈和修改意见

🤖 **智能体团队**：
- 🏗️ **A - StructureExtractor**: 结构抽取，从招标文件提取投标文件格式要求，生成投标文件骨架
- 📋 **B - SpecExtractor**: 技术规格书抽取，精准定位并提取第四章技术规格书内容

💼 **当前工作流程**：
A：结构抽取 → B：技术规格书

📊 **状态管理**：使用 ✅已完成、🚧进行中、⏳待处理 来标记任务状态

🎯 **目标**: 通过该工作流帮助用户高效处理招标文件，生成基础的投标文件骨架和技术规格书。"""
    
    async def execute(self, context: AgentContext) -> AgentResponse:
        try:
            # 分析用户请求，判断是否需要处理招标文件
            analysis = await self._analyze_user_request(context)
            
            session_state = context.project_state or {}
            current_stage = session_state.get("current_stage", "initial")
            
            # 根据当前阶段决定下一步行动
            if current_stage == "initial":
                return await self._handle_initial_request(context)
            elif current_stage in ("parsing_requested", "parsing_completed"):
                # 处理文档解析请求或解析完成后继续执行工作流
                context.project_state["current_stage"] = "document_parsing" if current_stage == "parsing_requested" else current_stage
                return await self._coordinate_bid_build(context)
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

    async def _handle_initial_request(self, context: AgentContext) -> AgentResponse:
        """处理初始请求"""
        analysis = await self._analyze_user_request(context)
        
        if analysis["action"] in ["process_bidding_documents", "process_documents"]:
            # 开始招标文件处理流程，直接触发工作流
            return await self._coordinate_bid_build(context)
        else:
            # 一般对话处理
            return await self._handle_general_coordination(context)
    
    async def _handle_general_coordination(self, context: AgentContext) -> AgentResponse:
        """处理一般性协调请求"""
        user_text = (context.user_input or "").strip()
        current_stage = context.project_state.get("current_stage", "initial")

        # 简易确认语义：允许用户在对话中确认各阶段产物
        confirm_map = {
            "确认招标文件": ("tender_confirmed", True),
            "确认骨架": ("outline_confirmed", True),
            "确认规格书": ("spec_confirmed", True),
        }
        for kw, (key, val) in confirm_map.items():
            if kw in user_text:
                context.project_state[key] = val
                return AgentResponse(
                    content=f"✅ 已设置 {key} = {val}。可继续下一步。",
                    metadata={"current_agent": "coordinator", "stage": context.project_state.get("current_stage", "general_coordination")},
                    next_actions=["await_user_input"],
                )

        # 明确的“生成技术方案”意图
        plan_triggers = ["技术方案", "生成方案", "编写方案", "生成技术方案", "方案编写"]
        if any(k in user_text for k in plan_triggers):
            return await self._handle_plan_request(context)

        # 触发词：继续执行/开始/执行/生成模板 → 直接推进到工作流
        trigger_keywords = ["继续", "继续执行", "开始", "执行", "生成模板"]
        if any(k in user_text for k in trigger_keywords):
            return await self._coordinate_bid_build(context)

        # === 修复6: 堵住协调器的"误改阶段" ===
        # 只有当当前阶段不是其它专用阶段时，才设置为 general_coordination
        if current_stage in (None, "", "initial", "general_coordination"):
            md_stage = "general_coordination"
        else:
            md_stage = current_stage  # 不覆盖专用阶段

        return AgentResponse(
            content="🤝 **Coordinator 智能体**: 我来协助您处理招标文件相关事务。\n\n请上传招标文件或告诉我您的具体需求，我会协调专业团队为您处理。",
            metadata={
                "current_agent": "coordinator",
                "stage": md_stage  # 使用保护后的阶段
            },
            next_actions=["await_user_input"]
        )

    async def _handle_plan_request(self, context: AgentContext) -> AgentResponse:
        """根据规格书和用户要求生成技术方案（仅生成 技术方案.md，不再自动拼装或校验）"""
        # 确保已具备基础产物（骨架与规格书）
        from app_core.config import settings
        wiki_dir = settings.WIKI_DIR
        tender_path = (context.project_state or {}).get("tender_path")

        # 如未提取过结构与规格书，则先执行简化工作流
        outline_path = (context.project_state or {}).get("outline_path")
        spec_path = (context.project_state or {}).get("spec_path")
        if not (outline_path and spec_path):
            # 若还没解析过，但上传了文件，则先调用解析器
            if context.uploaded_files and not tender_path:
                from .document_parser import DocumentParserAgent
                parser = DocumentParserAgent()
                parse_result = await parser.execute(context)
                if parse_result and parse_result.metadata.get("tender_path"):
                    tender_path = parse_result.metadata.get("tender_path")
                    context.project_state["tender_path"] = tender_path
                    context.project_state.setdefault("files_to_create", []).extend(
                        parse_result.metadata.get("files_to_create", [])
                    )
            try:
                rb = run_build(
                    session_id=context.project_state.get("session_id", "coordinator-session"),
                    tender_path=tender_path or settings.TENDER_DEFAULT_PATH,
                    wiki_dir=wiki_dir,
                    meta=context.project_state.get("meta", {})
                )
                outline_path = rb.get("outline_path")
                spec_path = rb.get("spec_path")
                context.project_state.update({
                    "outline_path": outline_path,
                    "spec_path": spec_path,
                })
            except Exception as e:
                return AgentResponse(
                    content=f"无法生成技术方案：前置产物缺失且构建失败（{e}）",
                    status="error",
                    metadata={"current_agent": "coordinator", "stage": "failed"}
                )

        # 生成技术方案（核心依据：技术规格书_提取.md；参考：招标文件.md）
        st = {
            "wiki_dir": wiki_dir,
            "spec_path": spec_path,
            "tender_path": tender_path or settings.TENDER_DEFAULT_PATH,
            "user_input": context.user_input,
            "meta": context.project_state.get("meta", {}),
        }
        st = PlanOutliner().execute(st)
        plan_path = st.get("plan_path")

        # 回写状态
        context.project_state.update({
            "plan_path": plan_path,
            "current_stage": "plan_created",
        })

        created_lines = []
        if outline_path:
            created_lines.append(f"- 投标文件_骨架.md: {outline_path}")
        if spec_path:
            created_lines.append(f"- 技术规格书_提取.md: {spec_path}")
        if plan_path:
            created_lines.append(f"- 技术方案.md: {plan_path}")
        msg = "\n".join([
            "🛠️ 已根据您的要求生成技术方案：",
            *created_lines,
            "\n请先检查：",
            "1) 招标文件.md 是否正确（如需更换，请重新上传并输入“重新生成”）",
            "2) 投标文件_骨架.md 是否符合格式要求（回复“确认骨架”继续）",
            "3) 技术规格书_提取.md 是否准确（回复“确认规格书”继续）",
            "4) 若需要按特定要求调整方案，请直接说明，我会重新生成对应部分。",
        ])

        files_created = [
            {"name": "投标文件_骨架.md", "path": outline_path} if outline_path else None,
            {"name": "技术规格书_提取.md", "path": spec_path} if spec_path else None,
            {"name": "技术方案.md", "path": plan_path} if plan_path else None,
        ]
        files_created = [f for f in files_created if f]

        return AgentResponse(
            content=msg,
            metadata={
                "current_agent": "coordinator",
                "stage": "plan_created",
                "action": "plan_created",
                "files_to_create": files_created,
            },
            next_actions=[],
        )

    async def _coordinate_bid_build(self, context: AgentContext) -> AgentResponse:
        """协调简化版工作流（结构→规格）"""
        context.project_state = context.project_state or {}
        
        # 检查是否有上传文件且未进行文档解析
        has_uploaded_files = bool(context.uploaded_files)
        has_parsed_wiki_file = "tender_path" in context.project_state and context.project_state.get("tender_path", "").startswith("wiki/")
        
        # 如果有上传文件但还没进行文档解析，先调用DocumentParserAgent
        if has_uploaded_files and not has_parsed_wiki_file:
            from .document_parser import DocumentParserAgent
            parser = DocumentParserAgent()
            parse_result = await parser.execute(context)
            
            # 更新project_state中的tender_path
            if "tender_path" in parse_result.metadata:
                context.project_state["tender_path"] = parse_result.metadata["tender_path"]
                
            # 更新files_to_create
            if "files_to_create" in parse_result.metadata:
                context.project_state["files_to_create"] = parse_result.metadata["files_to_create"]
            
            # 返回解析结果，让用户知道文档已解析完成
            return AgentResponse(
                content=parse_result.content + "\n\n🚀 **接下来将启动工作流进行投标文件生成...**",
                metadata={
                    "current_agent": "document_parser",
                    "stage": "parsing_completed",  # 使用完成状态而不是进行中状态
                    "action": "parsing_completed",
                    "files_to_create": parse_result.metadata.get("files_to_create", []),
                    "tender_path": parse_result.metadata.get("tender_path"),
                },
                next_actions=[]  # 清空next_actions避免继续循环
            )
        
        # 如果没有上传文件，直接使用默认模板执行工作流
        # 优先使用文档解析产出的标准路径；若不存在，则依然允许流程以兜底模板运行
        from app_core.config import settings
        tender_path = (
            (context.project_state or {}).get("tender_path")
            or settings.TENDER_DEFAULT_PATH
        )
        wiki_dir = settings.WIKI_DIR
        meta = context.project_state.get("meta", {}) if isinstance(context.project_state, dict) else {}

        try:
            result = run_build(session_id=context.project_state.get("session_id", "coordinator-session"), tender_path=tender_path, wiki_dir=wiki_dir, meta=meta)
            # 写回关键路径到状态
            context.project_state.update({
                "outline_path": result.get("outline_path"),
                "spec_path": result.get("spec_path"),
                "current_stage": "bid_build_completed",
            })

            # 生成用户提示
            created = [
                ("投标文件_骨架.md", result.get("outline_path")),
                ("技术规格书_提取.md", result.get("spec_path")),
            ]
            lines = [f"- {name}: {path}" for name, path in created if path]
            msg = "\n".join(["✅ 已生成以下文件:"] + lines)

            return AgentResponse(
                content=msg,
                metadata={
                    "current_agent": "coordinator",
                    "stage": "bid_build_completed",
                    "action": "bid_build_completed",
                },
                next_actions=[],
            )
        except Exception as e:
            context.project_state["current_stage"] = "bid_build_failed"
            return AgentResponse(
                content=f"❌ 工作流执行失败: {str(e)}",
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
