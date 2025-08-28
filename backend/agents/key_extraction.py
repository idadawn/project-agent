from typing import Dict, Any, List
import json
import os
from .base import BaseAgent, AgentContext, AgentResponse


class KeyExtractionAgent(BaseAgent):
    def __init__(self):
        super().__init__("key_extraction")
    
    def get_system_prompt(self) -> str:
        return """您是一个专业的关键信息提取智能体，专门从解析后的招标文档中提取用户指定的关键信息。

您的主要职责：
1. 从解析后的文档中提取技术规格书（第四章）
2. 提取投标文件格式要求（第五章）
3. 识别其他重要的招标信息
4. 生成结构化的信息摘要

提取策略：
- 使用多种提示词识别目标章节（如"第四章 技术规格书"、"技术规格书"、"第4章 技术规格"等）
- 提取完整章节内容（包括子章节、表格、图片描述等）
- 识别章节边界，确保内容完整
- 处理文档格式变体和不规范标题

输出要求：
- 技术规格书：完整的技术要求和规格说明
- 投标文件格式：详细的文件结构和格式要求
- 其他关键信息：项目背景、评标标准、时间要求等
- 提供信息来源和页码标注"""
    
    async def execute(self, context: AgentContext) -> AgentResponse:
        try:
            extracted_info = {}
            
            # 从wiki文件夹读取解析后的文档
            parsed_files = self._get_parsed_files()
            
            for parsed_file in parsed_files:
                from backend.app_core.config import settings
                file_path = os.path.join(settings.WIKI_DIR, parsed_file)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        parsed_doc = json.load(f)
                    
                    # 提取关键信息
                    file_info = await self._extract_key_information(parsed_doc)
                    extracted_info[parsed_file] = file_info
            
            # 回退策略：若未生成结构化JSON，直接从 wiki/招标文件.md 提取
            if not extracted_info:
                from backend.app_core.config import settings
                wiki_path = os.path.join(settings.WIKI_DIR, "招标文件.md")
                if os.path.exists(wiki_path):
                    with open(wiki_path, 'r', encoding='utf-8') as f:
                        md_content = f.read()
                    file_info = await self._extract_from_markdown(md_content, filename="招标文件.md")
                    extracted_info["招标文件.md"] = file_info
            
            # 生成综合信息摘要
            summary = await self._generate_summary(extracted_info)
            
            return AgentResponse(
                content=summary,
                metadata={
                    "extracted_info": extracted_info,
                    "total_files_processed": len(extracted_info)
                },
                status="completed"
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"关键信息提取失败: {str(e)}",
                status="error"
            )
    
    def _get_parsed_files(self) -> List[str]:
        """获取wiki文件夹中的所有JSON文件"""
        from backend.app_core.config import settings
        parsed_dir = settings.WIKI_DIR
        if not os.path.exists(parsed_dir):
            return []
        
        return [f for f in os.listdir(parsed_dir) if f.endswith('.json')]
    
    async def _extract_key_information(self, parsed_doc: Dict[str, Any]) -> Dict[str, Any]:
        """从单个解析文档中提取关键信息"""
        structure = parsed_doc.get('structure', [])
        filename = parsed_doc.get('filename', 'unknown')
        
        # 查找技术规格书
        tech_specs = await self._find_tech_specifications(structure)
        
        # 查找投标文件格式
        bid_format = await self._find_bid_format(structure)
        
        # 查找其他关键信息
        other_info = await self._find_other_key_info(structure)
        
        return {
            "filename": filename,
            "tech_specifications": tech_specs,
            "bid_format": bid_format,
            "other_key_info": other_info,
            "extraction_timestamp": self._get_timestamp()
        }
    
    async def _find_tech_specifications(self, structure: List[Dict[str, Any]]) -> Dict[str, Any]:
        """查找技术规格书章节"""
        tech_keywords = [
            "技术规格书",
            "技术规格",
            "技术说明书",
            "技术要求",
        ]
        
        tech_section = self._find_section_by_keywords(structure, tech_keywords)
        
        if tech_section:
            # 使用LLM详细分析技术规格书内容
            analysis = await self._analyze_tech_specs(tech_section)
            return {
                "found": True,
                "title": tech_section.get('title', ''),
                "content": tech_section.get('content', ''),
                "page": tech_section.get('page', ''),
                "analysis": analysis,
                "subsections": tech_section.get('subsections', [])
            }
        
        return {
            "found": False,
            "message": "未找到技术规格书章节"
        }
    
    async def _find_bid_format(self, structure: List[Dict[str, Any]]) -> Dict[str, Any]:
        """查找投标文件格式章节"""
        format_keywords = [
            "投标文件格式",
            "格式要求",
            "文件格式要求",
            "投标格式",
        ]
        
        format_section = self._find_section_by_keywords(structure, format_keywords)
        
        if format_section:
            # 使用LLM分析投标文件格式要求
            analysis = await self._analyze_bid_format(format_section)
            return {
                "found": True,
                "title": format_section.get('title', ''),
                "content": format_section.get('content', ''),
                "page": format_section.get('page', ''),
                "analysis": analysis,
                "subsections": format_section.get('subsections', [])
            }
        
        return {
            "found": False,
            "message": "未找到投标文件格式章节"
        }
    
    async def _find_other_key_info(self, structure: List[Dict[str, Any]]) -> Dict[str, Any]:
        """查找其他关键信息"""
        key_info = {
            "project_background": None,
            "evaluation_criteria": None,
            "timeline": None,
            "budget": None,
            "contact_info": None
        }
        
        # 查找项目背景
        background_keywords = ["项目背景", "项目概述", "项目简介", "第一章", "第二章"]
        background_section = self._find_section_by_keywords(structure, background_keywords)
        if background_section:
            key_info["project_background"] = {
                "title": background_section.get('title', ''),
                "content": background_section.get('content', '')[:1000]
            }
        
        # 查找评标标准
        eval_keywords = ["评标标准", "评标方法", "评分标准", "评审标准"]
        eval_section = self._find_section_by_keywords(structure, eval_keywords)
        if eval_section:
            key_info["evaluation_criteria"] = {
                "title": eval_section.get('title', ''),
                "content": eval_section.get('content', '')[:1000]
            }
        
        return key_info
    
    def _find_section_by_keywords(self, structure: List[Dict[str, Any]], keywords: List[str]) -> Dict[str, Any]:
        """根据关键词查找章节。避免将仅有“第X章”而无具体标题的章节作为命中。"""

        def is_generic_chapter(title: str) -> bool:
            import re
            t = title.strip()
            # "第X章" 或 "第X章 目录" 等无明确主题的，判定为泛化
            return bool(re.fullmatch(r"第[一二三四五六七八九十百]+章\s*", t))

        for section in structure:
            title = (section.get('title', '') or '').strip()
            if not title:
                continue

            if not is_generic_chapter(title):
                normalized = title.replace(' ', '')
                for keyword in keywords:
                    if keyword and keyword.replace(' ', '') in normalized:
                        return section

            # 递归查找子章节
            subsections = section.get('subsections', [])
            if subsections:
                found = self._find_section_by_keywords(subsections, keywords)
                if found:
                    return found
        return None
    
    async def _analyze_tech_specs(self, tech_section: Dict[str, Any]) -> str:
        """分析技术规格书内容"""
        content = tech_section.get('content', '')
        
        analysis_prompt = f"""请分析以下技术规格书内容，提取关键技术要求：

{content[:2000]}

请提供：
1. 主要技术指标和要求
2. 性能参数
3. 硬件/软件要求
4. 技术标准和规范
5. 兼容性要求
"""
        
        try:
            analysis = await self.llm_client.generate([
                {"role": "system", "content": "您是技术规格分析专家。"},
                {"role": "user", "content": analysis_prompt}
            ])
            return analysis
        except:
            return "技术规格分析暂时不可用"
    
    async def _analyze_bid_format(self, format_section: Dict[str, Any]) -> str:
        """分析投标文件格式要求"""
        content = format_section.get('content', '')
        
        analysis_prompt = f"""请分析以下投标文件格式要求，提取关键格式信息：

{content[:2000]}

请提供：
1. 文件结构要求
2. 必填章节和内容
3. 格式规范（页面设置、字体等）
4. 提交要求（份数、装订等）
5. 其他特殊要求
"""
        
        try:
            analysis = await self.llm_client.generate([
                {"role": "system", "content": "您是投标文件格式分析专家。"},
                {"role": "user", "content": analysis_prompt}
            ])
            return analysis
        except:
            return "格式要求分析暂时不可用"
    
    async def _generate_summary(self, extracted_info: Dict[str, Any]) -> str:
        """生成综合信息摘要"""
        summary_parts = []
        
        summary_parts.append("## 关键信息提取结果\n")
        
        for filename, info in extracted_info.items():
            summary_parts.append(f"### 文件：{info.get('filename', filename)}\n")
            
            # 技术规格书信息
            tech_specs = info.get('tech_specifications', {})
            if tech_specs.get('found'):
                summary_parts.append("**✅ 技术规格书：已找到**")
                summary_parts.append(f"- 章节：{tech_specs.get('title', '')}")
                summary_parts.append(f"- 页码：{tech_specs.get('page', '')}")
                summary_parts.append(f"- 分析：{tech_specs.get('analysis', '')[:200]}...\n")
            else:
                summary_parts.append("**❌ 技术规格书：未找到**\n")
            
            # 投标文件格式信息
            bid_format = info.get('bid_format', {})
            if bid_format.get('found'):
                summary_parts.append("**✅ 投标文件格式：已找到**")
                summary_parts.append(f"- 章节：{bid_format.get('title', '')}")
                summary_parts.append(f"- 页码：{bid_format.get('page', '')}")
                summary_parts.append(f"- 分析：{bid_format.get('analysis', '')[:200]}...\n")
            else:
                summary_parts.append("**❌ 投标文件格式：未找到**\n")
            
            summary_parts.append("---\n")
        
        return "\n".join(summary_parts)
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.now().isoformat()

    async def _extract_from_markdown(self, md_text: str, filename: str = "unknown.md") -> Dict[str, Any]:
        """基于Markdown标题结构的稳健解析：
        - 支持 ATX 标题（#、##、###）
        - 支持中文章标题：“第X章 标题”
        - 以相同或更高层级的下一个标题作为边界切分
        """
        import re

        text = md_text.replace("**", "")

        # 收集标题（位置、层级、标题文本）
        headings: List[Dict[str, Any]] = []
        for m in re.finditer(r"^(#{1,6})\s*(.+)$", text, flags=re.M):
            level = len(m.group(1))
            title = m.group(2).strip()
            headings.append({"idx": m.start(), "level": level, "title": title})

        # 同时支持“第X章 标题”样式，视为一级标题
        for m in re.finditer(r"^第[一二三四五六七八九十百]+章\s*([^\n]+)$", text, flags=re.M):
            title = m.group(0).strip()  # 保留完整“第X章 标题”
            headings.append({"idx": m.start(), "level": 1, "title": title})

        if not headings:
            # 无法解析标题时，整体作为一个区块
            parsed_doc = {"filename": filename, "structure": [{"title": "全文", "content": text, "subsections": []}]}
            return await self._extract_key_information(parsed_doc)

        # 按出现顺序排序
        headings.sort(key=lambda h: h["idx"])

        # 构造分段
        sections: List[Dict[str, Any]] = []
        for i, h in enumerate(headings):
            start = h["idx"]
            level = h["level"]
            title = h["title"]
            # 找到下一个同级或更高级标题作为结束
            end = len(text)
            for j in range(i + 1, len(headings)):
                if headings[j]["level"] <= level:
                    end = headings[j]["idx"]
                    break
            content = text[start:end].strip()
            sections.append({"level": level, "title": title, "content": content, "subsections": []})

        # 简化为平铺结构供关键词检索
        parsed_doc = {"filename": filename, "structure": sections}
        return await self._extract_key_information(parsed_doc)