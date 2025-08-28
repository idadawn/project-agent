from typing import Dict, Any, List
import os
from .base import BaseAgent, AgentContext, AgentResponse


class BidGeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("bid_generator")
    
    def get_system_prompt(self) -> str:
        return """您是一个专业的投标文件生成智能体，专门根据提取的关键信息和用户输入生成符合要求的投标文件。

您的主要职责：
1. 基于技术规格书生成技术方案
2. 根据投标文件格式要求构建文档结构
3. 生成"方案详细说明及施工组织设计"部分
4. 支持用户交互修改和补充内容
5. 输出最终的投标文件.md 文件

生成规范：
- 严格按照招标文件的格式要求
- 技术方案要针对性强，满足所有技术指标
- 内容专业、完整、逻辑清晰
- 支持多种输出格式（MD/DOCX/PDF）

文档结构：
1. 项目概述
2. 技术方案设计
3. 实施计划和组织架构
4. 质量保证体系
5. 风险管理和应对措施
6. 预算和报价
7. 服务承诺"""
    
    async def execute(self, context: AgentContext) -> AgentResponse:
        try:
            # 获取提取的关键信息
            extracted_info = context.extracted_info
            
            if not extracted_info:
                return AgentResponse(
                    content="❌ **关键信息缺失**\n\n缺少解析后的文档信息，无法生成投标方案。\n\n请先完成文档解析和关键信息提取步骤。",
                    status="error",
                    metadata={
                        "error_type": "missing_extracted_info",
                        "required_steps": ["document_parsing", "key_extraction"]
                    }
                )
            
            # 检查关键信息是否完整
            missing_info = self._check_missing_critical_info(extracted_info)
            has_bid_format = self._has_bid_format(extracted_info)
            allow_skeleton = (missing_info and has_bid_format)
            
            # 生成投标方案
            if allow_skeleton:
                proposal_content = await self._generate_skeleton_from_bid_format(extracted_info)
            else:
                if missing_info:
                    return AgentResponse(
                        content=f"❌ **关键信息不完整**\n\n以下关键信息缺失，无法生成有效的投标方案：\n\n{missing_info}\n\n请检查上传的招标文件是否包含这些必要信息。",
                        status="error",
                        metadata={
                            "error_type": "incomplete_critical_info",
                            "missing_info": missing_info
                        }
                    )
                proposal_content = await self._generate_proposal(extracted_info, context.user_input)
            
            # 保存到投标文件文件夹（与“解析文件”同级）
            proposal_dir = "/root/project/git/project-agent/投标文件"
            os.makedirs(proposal_dir, exist_ok=True)
            proposal_path = os.path.join(proposal_dir, "投标文件.md")
            with open(proposal_path, 'w', encoding='utf-8') as f:
                f.write(proposal_content)
            
            return AgentResponse(
                content=f"投标方案生成完成，已保存到 投标文件.md\n\n{proposal_content[:500]}...",
                metadata={
                    "proposal_file": "投标文件.md",
                    "content_length": len(proposal_content),
                    # 通过 files_to_create 把文件内容回传给前端与会话存储
                    "files_to_create": [
                        {
                            "name": "投标文件.md",
                            "content": proposal_content,
                            "type": "proposal",
                            "folder": "proposal"
                        }
                    ]
                },
                status="completed"
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"投标文件生成失败: {str(e)}",
                status="error"
            )
    
    async def _generate_proposal(self, extracted_info: Dict[str, Any], user_input: str) -> str:
        """生成完整的投标方案"""
        
        # 分析提取的信息
        tech_requirements = self._extract_tech_requirements(extracted_info)
        bid_format = self._extract_bid_format(extracted_info)
        project_context = self._extract_project_context(extracted_info)
        
        # 生成方案大纲
        outline = await self._generate_outline(tech_requirements, bid_format, user_input)
        
        # 生成详细内容
        detailed_content = await self._generate_detailed_content(outline, tech_requirements, project_context, user_input)
        
        return detailed_content
    
    def _extract_tech_requirements(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """提取技术要求"""
        tech_requirements = {
            "specifications": [],
            "performance_requirements": [],
            "technical_standards": [],
            "compatibility_requirements": []
        }
        
        for file_info in extracted_info.values():
            tech_specs = file_info.get('tech_specifications', {})
            if tech_specs.get('found'):
                tech_requirements["specifications"].append({
                    "title": tech_specs.get('title', ''),
                    "content": tech_specs.get('content', ''),
                    "analysis": tech_specs.get('analysis', '')
                })
        
        return tech_requirements
    
    def _extract_bid_format(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """提取投标格式要求"""
        bid_format = {
            "structure_requirements": [],
            "format_specifications": [],
            "submission_requirements": []
        }
        
        for file_info in extracted_info.values():
            format_info = file_info.get('bid_format', {})
            if format_info.get('found'):
                bid_format["structure_requirements"].append({
                    "title": format_info.get('title', ''),
                    "content": format_info.get('content', ''),
                    "analysis": format_info.get('analysis', '')
                })
        
        return bid_format
    
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
    
    def _extract_project_context(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """提取项目背景信息"""
        context = {
            "background": "",
            "objectives": "",
            "constraints": "",
            "evaluation_criteria": ""
        }
        
        for file_info in extracted_info.values():
            other_info = file_info.get('other_key_info', {})
            
            if other_info.get('project_background'):
                context["background"] = other_info['project_background'].get('content', '')
            
            if other_info.get('evaluation_criteria'):
                context["evaluation_criteria"] = other_info['evaluation_criteria'].get('content', '')
        
        return context
    
    async def _generate_outline(self, tech_requirements: Dict[str, Any], bid_format: Dict[str, Any], user_input: str) -> str:
        """生成投标方案大纲"""
        
        outline_prompt = f"""基于以下信息生成投标方案大纲：

用户需求：
{user_input}

技术要求：
{str(tech_requirements)[:1000]}

投标格式要求：
{str(bid_format)[:1000]}

请生成详细的投标方案大纲，包括：
1. 项目概述和理解
2. 技术方案设计
3. 实施计划和时间安排
4. 团队组织和人员配置
5. 质量保证体系
6. 风险管理和控制措施
7. 项目预算和成本控制
8. 售后服务和技术支持

每个章节请提供2-3个子章节。
"""
        
        outline = await self.llm_client.generate([
            {"role": "system", "content": "您是专业的投标方案规划专家。"},
            {"role": "user", "content": outline_prompt}
        ])
        
        return outline
    
    async def _generate_detailed_content(self, outline: str, tech_requirements: Dict[str, Any], 
                                       project_context: Dict[str, Any], user_input: str) -> str:
        """生成详细的投标方案内容"""
        
        content_prompt = f"""基于以下大纲和要求，生成完整的投标方案内容：

大纲：
{outline}

技术要求：
{str(tech_requirements)[:1500]}

项目背景：
{str(project_context)[:1000]}

用户需求：
{user_input}

请生成完整、专业的投标方案，要求：
1. 内容详实，针对性强
2. 技术方案满足所有技术指标
3. 实施方案具有可操作性
4. 风险控制措施完善
5. 符合招标文件的格式要求
6. 使用Markdown格式

请确保方案的专业性和完整性。
"""
        
        content = await self.llm_client.generate([
            {"role": "system", "content": "您是资深的投标方案撰写专家，擅长编写高质量的技术投标方案。"},
            {"role": "user", "content": content_prompt}
        ])
        
        # 添加文档头部信息
        header = f"""# 投标方案 - {self._get_project_name(project_context)}

> 生成时间：{self._get_timestamp()}
> 基于招标文件自动生成

---

"""
        
        return header + content
    
    def _get_project_name(self, project_context: Dict[str, Any]) -> str:
        """从项目背景中提取项目名称"""
        background = project_context.get('background', '')
        if background:
            # 简单的项目名称提取逻辑
            lines = background.split('\n')
            for line in lines[:5]:
                if '项目' in line and len(line) < 100:
                    return line.strip()
        
        return "技术方案项目"
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

    def _has_bid_format(self, extracted_info: Dict[str, Any]) -> bool:
        for file_info in extracted_info.values():
            fmt = file_info.get('bid_format', {})
            if fmt.get('found'):
                return True
        return False

    async def _generate_skeleton_from_bid_format(self, extracted_info: Dict[str, Any]) -> str:
        """基于投标文件格式生成“投标文件.md”主体框架（占位内容）。"""
        # 聚合一份格式内容
        format_content = ""
        for file_info in extracted_info.values():
            fmt = file_info.get('bid_format', {})
            if fmt.get('found'):
                format_content = fmt.get('content', '')
                break

        sections = [
            "投标函",
            "法定代表人身份证明",
            "授权委托书",
            "投标保证金",
            "投标报价表",
            "分项报价表",
            "企业资料",
            "方案详细说明及施工组织设计",
            "资格审查资料",
            "商务和技术偏差表",
            "其他资料"
        ]

        header = f"""# 投标文件（主体框架）

> 生成时间：{self._get_timestamp()}
> 本文件根据“第五章 投标文件格式”自动生成骨架，请逐项补充。

---

## 目录
"""
        header += "\n".join([f"- {idx+1}. {title}" for idx, title in enumerate(sections)]) + "\n\n---\n\n"

        body_parts: List[str] = []
        for title in sections:
            body_parts.append(f"## {title}\n\n> 待补充：根据招标文件要求填写本章节的具体内容。\n")

        appendix = ""
        if format_content:
            appendix = "\n---\n\n> 附：原始‘投标文件格式’参考（来源：第五章 内容节选）\n\n" + format_content[:4000]

        return header + "\n".join(body_parts) + appendix