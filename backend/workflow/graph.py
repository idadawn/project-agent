"""
主工作流引擎 - 实现基于阶段的智能体路由和循环控制
"""
import asyncio
from typing import Dict, Any, Optional
from agents.coordinator import CoordinatorAgent
from agents.document_parser import DocumentParserAgent
from agents.base import AgentContext
from workflow.bid_build_graph import run_build_async


class ProposalWorkflow:
    """提案工作流管理器 - 核心修复：基于阶段的显式路由"""
    
    def __init__(self):
        self.coordinator = CoordinatorAgent()
        self.document_parser = DocumentParserAgent()
        self.max_iterations = 8  # 降低递归限制，fail fast
        
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _should_continue(self, state: dict) -> bool:
        """判断是否继续执行工作流"""
        stage = state.get("current_stage", "initial")
        
        # 终止条件
        if stage in {"final", "done", "responded", "bid_build_completed", "bid_build_failed"}:
            return False
            
        # 环路保险丝：同一阶段重复3次后强制退出
        stage_key = f"_stage_count_{stage}"
        stage_count = state.get(stage_key, 0) + 1
        state[stage_key] = stage_count
        
        if stage_count >= 3:
            print(f"DEBUG: Stage '{stage}' repeated {stage_count} times, forcing exit")
            state["current_stage"] = "failed"
            state["error"] = "stalled-stage"
            return False
            
        return True
    
    async def run(self, initial_state: dict) -> dict:
        """
        执行工作流 - 核心修复：基于阶段的显式路由
        """
        state = initial_state.copy()
        iteration = 0
        
        print(f"DEBUG: Starting workflow with state: {list(state.keys())}")
        
        while iteration < self.max_iterations and self._should_continue(state):
            iteration += 1
            current_stage = state.get("current_stage", "initial")
            
            print(f"DEBUG: Iteration {iteration}, current_stage: {current_stage}")
            
            # === 修复1: 阶段提升逻辑（应用 next_stage） ===
            prev = state.get("current_stage")
            ns = state.pop("next_stage", None)
            if ns and ns != prev:
                print(f"DEBUG: Promoting stage via next_stage: {prev} → {ns}")
                state["current_stage"] = ns
                # 重置该阶段计数，避免误触"重复3次退出"
                state.pop(f"_stage_count_{prev}", None)
                current_stage = ns
            
            # === 修复2: 自动触发解析逻辑，移到协调器执行之前，只触发一次 ===
            if (state.get("uploaded_files") 
                and not state.get("files_parsed")               # 解析完成后不再触发
                and not state.get("parsing_auto_triggered")     # 只触发一次
                and current_stage in (None, "", "initial", "general_coordination")):
                print("DEBUG: Auto-trigger parsing once → set document_parsing")
                state["parsing_auto_triggered"] = True
                state["current_stage"] = "document_parsing"     # 直接进入解析阶段
                current_stage = "document_parsing"
            
            # === 修复2: 基于阶段的显式路由 - 核心修复！===
            # 当 current_stage == "document_parsing" 时，绝不能再调用协调器
            # 应当直接调"文档解析"节点（DocumentParserAgent）
            if current_stage == "document_parsing":
                print(f"DEBUG: Routing to DocumentParserAgent for stage: {current_stage}")
                response = await self._execute_document_parser(state)
            elif current_stage in ("bid_build_ready", "planning"):
                # A-E 工作流阶段：进入投标方案生成
                print(f"DEBUG: Routing to BidBuildWorkflow for stage: {current_stage}")
                response = await self._execute_bid_build_workflow(state)
            elif current_stage in ("research", "evidence_gathering"):
                print(f"DEBUG: Routing to Coordinator for research stage: {current_stage}")
                response = await self._execute_coordinator(state)
            elif current_stage in ("drafting", "proposal_writing"):
                print(f"DEBUG: Routing to Coordinator for drafting stage: {current_stage}")
                response = await self._execute_coordinator(state)
            elif current_stage in ("review", "optimize", "finalize"):
                print(f"DEBUG: Routing to Coordinator for review stage: {current_stage}")
                response = await self._execute_coordinator(state)
            else:
                # 其余阶段才找协调器
                print(f"DEBUG: Routing to Coordinator for stage: {current_stage}")
                response = await self._execute_coordinator(state)
            
            # 更新状态
            if hasattr(response, 'metadata') and response.metadata:
                # 更新stage，但不要让协调器误改document_parsing阶段
                if "stage" in response.metadata:
                    new_stage = response.metadata["stage"]
                    # 保护机制：如果当前是document_parsing且解析器返回了明确的下一阶段，才允许更新
                    if current_stage == "document_parsing":
                        if new_stage in ("parsing_completed", "bid_build_ready", "planning"):
                            state["current_stage"] = new_stage
                            print(f"DEBUG: DocumentParser updated stage: {current_stage} → {new_stage}")
                        else:
                            print(f"DEBUG: Ignoring stage update from DocumentParser: {new_stage}")
                    else:
                        # 非解析阶段，正常更新
                        state["current_stage"] = new_stage
                        print(f"DEBUG: Stage updated: {current_stage} → {new_stage}")
                
                # 合并其他元数据
                for key, value in response.metadata.items():
                    if key not in ["stage"]:  # stage已单独处理
                        state[key] = value
            
            # 添加到对话历史
            if hasattr(response, 'content') and response.content:
                state.setdefault("conversation_history", []).append({
                    "role": "assistant",
                    "content": response.content,
                    "metadata": getattr(response, 'metadata', {}),
                    "timestamp": self._get_timestamp()
                })
        
        if iteration >= self.max_iterations:
            print(f"DEBUG: Workflow stopped after {iteration} iterations (max limit)")
            state["current_stage"] = "failed"
            state["error"] = "max-iterations"
        
        print(f"DEBUG: Workflow completed. Final stage: {state.get('current_stage')}")
        return state
    
    def _resolve_tender_source(self, state: dict):
        """统一解析招标文件来源，返回 (src_type, src, filename)"""
        from pathlib import Path
        
        # 1) 优先：内存内容
        if state.get("tender_md"):
            filename = Path(state.get("tender_path", "招标文件.md")).name
            return "INLINE", state["tender_md"], filename

        # 2) 其次：绝对路径
        p = state.get("tender_path")
        if p and Path(p).exists():
            p = Path(p).resolve()
            return "FILE", p, p.name

        # 3) 再退回 parsed_files 列表
        for p in state.get("parsed_files", []):
            q = Path(p)
            if q.exists():
                return "FILE", q.resolve(), q.name

        # 4) 兜底：常见目录候选
        for c in [
            Path("wiki") / "招标文件.md",
            Path("/root/project/git/project-agent/wiki") / "招标文件.md",
            Path("/root/project/git/project-agent/uploads") / "招标文件.md",
        ]:
            if c.exists():
                return "FILE", c.resolve(), c.name

        raise FileNotFoundError("未找到招标文件：tender_md/tender_path/parsed_files/candidates 均不存在")
    
    def _register_outputs(self, state: dict) -> None:
        """集中注册 A–E 产物到 state['files_to_create']（只追加，不覆盖）。"""
        from pathlib import Path
        # 仅追加
        outputs = state.setdefault("files_to_create", [])

        # 产物键 → 展示名
        mapping = [
            ("outline_path",       "投标文件_骨架.md"),
            ("spec_path",          "技术规格书_提取.md"),
            ("plan_path",          "方案_提纲.md"),
            ("plan_draft_path",    "投标文件_草案.md"),
            ("draft_path",         "投标文件_草案.md"),
            ("sanity_report_path", "一致性检查报告.md"),
        ]

        # 原始招标MD（如有且为md）也可回传便于检查/引用
        tender_path = state.get("tender_path")
        if tender_path:
            tp = Path(tender_path)
            if tp.exists() and tp.is_file() and tp.name.endswith(".md"):
                mapping.insert(0, ("tender_path", "招标文件.md"))

        items: list[dict] = []
        for key, display in mapping:
            p = state.get(key)
            if not p:
                continue
            q = Path(p)
            if q.exists() and q.is_file():
                items.append({"name": display, "path": str(q.resolve())})

        # 去重（同名同路径）
        seen = set()
        dedup = []
        for it in items:
            k = (it["name"], it["path"]) 
            if k in seen:
                continue
            seen.add(k)
            dedup.append(it)

        outputs.extend(dedup)
        print(f"[A-E] Registered outputs: {[i['name'] for i in dedup]}")

    async def _execute_bid_build_workflow(self, state: dict) -> Any:
        """执行 A-E 工作流（结构抽取→规格书→提纲→拼装→校验）"""
        try:
            from agents.base import AgentResponse
            from pathlib import Path
            import tempfile, shutil
            
            # 日志与自检
            print(f"[A-E] tender_path={state.get('tender_path')}")
            print(f"[A-E] tender_md_in_memory={'yes' if 'tender_md' in state else 'no'}")
            
            # 解析招标文件路径 - 使用新的统一方法
            src_type, src, filename = self._resolve_tender_source(state)
            print(f"[A-E] tender_md_in_memory={'yes' if src_type=='INLINE' else 'no'}")
            
            if src_type == "INLINE":
                # 为了兼容旧逻辑（仍然会去读路径），我们生成一个临时真实文件
                tmpdir = Path(tempfile.mkdtemp(prefix="tender_"))
                canonical = tmpdir / filename
                canonical.write_text(src, encoding="utf-8")
                print(f"[A-E] Created temp file for inline content: {canonical}")
            else:
                canonical = src  # 已是绝对路径
            
            print(f"[A-E] canonical path = {canonical}")
            
            # ✅ 兼容旧代码：在 uploads 下准备一份同名拷贝（或软链）
            # 这样即使某个子步骤仍然写死 'uploads/招标文件.md' 也不会再报错
            legacy_dir = Path("/root/project/git/project-agent/uploads")
            legacy_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(canonical, legacy_dir / filename)
            print(f"[A-E] Created legacy copy: {legacy_dir / filename}")
            
            session_id = state.get("session_id", "workflow-session")
            uploaded_files = state.get("uploaded_files", [])
            wiki_dir = "wiki"
            
            # 传给后续链路
            meta = {
                "tender_path": str(canonical),
                # 如需给子模块继续用 uploads/xxx，可同时给：
                "legacy_tender_path": str(legacy_dir / filename),
                "tender_filename": filename,
            }
            meta.update(state.get("meta", {}))
            print(f"DEBUG: Meta passed to A-E: {meta}")
            
            print(f"DEBUG: Starting A-E workflow for session: {session_id}")
            
            # 调用 A-E 工作流
            result = await run_build_async(
                session_id=session_id,
                uploaded_files=uploaded_files,
                wiki_dir=wiki_dir,
                meta=meta
            )
            
            # 更新状态
            state.update({
                "outline_path": result.get("outline_path"),
                "spec_path": result.get("spec_path"),
                "plan_path": result.get("plan_path"),
                "plan_draft_path": result.get("plan_draft_path"),
                "draft_path": result.get("draft_path"),
                "sanity_report_path": result.get("sanity_report_path"),
                "current_stage": "bid_build_completed",
            })
            
            # 收尾：集中注册产物，避免遗漏
            self._register_outputs(state)
            
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
            msg = "\n".join(["✅ 已完成A–E链路生成以下文件:"] + lines)
            
            return AgentResponse(
                content=msg,
                metadata={
                    "current_agent": "bid_build_workflow",
                    "stage": "bid_build_completed",
                    "action": "bid_build_completed",
                },
                next_actions=[],
            )
            
        except Exception as e:
            print(f"DEBUG: A-E workflow failed: {str(e)}")
            state["current_stage"] = "bid_build_failed"
            
            from agents.base import AgentResponse
            return AgentResponse(
                content=f"❌ A–E 工作流执行失败: {str(e)}",
                metadata={
                    "current_agent": "bid_build_workflow",
                    "stage": "bid_build_failed",
                },
                status="error",
                next_actions=[],
            )
    
    async def _execute_coordinator(self, state: dict) -> Any:
        """执行协调器"""
        context = AgentContext(
            user_input=state.get("user_input", ""),
            uploaded_files=state.get("uploaded_files", []),
            project_state=state
        )
        return await self.coordinator.execute(context)
    
    async def _execute_document_parser(self, state: dict) -> Any:
        """执行文档解析器"""
        context = AgentContext(
            user_input=state.get("user_input", ""),
            uploaded_files=state.get("uploaded_files", []),
            project_state=state
        )
        response = await self.document_parser.execute(context)
        
        # === 修复3: 解析器收尾：落锚"已解析"，推进到下一阶段 ===
        if hasattr(response, 'metadata') and response.metadata:
            # 确保解析成功后写入关键状态
            if response.metadata.get("action") == "parsing_completed":
                state["files_parsed"] = True               # 防止再次 auto-trigger
                state["parsing_auto_triggered"] = True     # 双保险
                # 推进到下个阶段
                if "tender_path" in response.metadata:
                    state["current_stage"] = "bid_build_ready"  # 或者 "planning"
                    print("DEBUG: DocumentParser completed, advancing to bid_build_ready")
        
        return response