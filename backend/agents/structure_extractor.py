from typing import Dict, Any, List, Tuple
import re, os, pathlib, datetime
from .base import BaseAgent

CANONICAL_SECTIONS = [
    "投标函","法定代表人身份证明","授权委托书","投标保证金",
    "投标报价表","分项报价表","企业资料","方案详细说明及施工组织设计",
    "资格审查资料","商务和技术偏差表","其他材料"
]

class StructureExtractor(BaseAgent):
    def __init__(self):
        super().__init__("structure_extractor")
    
    def get_system_prompt(self) -> str:
        return """你是一个专业的投标文件结构分析专家。你的任务是分析招标文件，提取投标文件的格式要求，生成标准化的投标文件骨架结构。"""

    def _find_bid_format_block(self, text: str) -> Tuple[int,int]:
        # 支持多写法：第五章/第5章/投标文件格式/投标文件格式（样式）
        start_pat = r"^#{1,6}\s*第\s*[五5V]\s*章.*?(投标文件格式|投标文件|投标文件格式[（(]样式[）)])"
        # 结束于"第六章|评标办法|其他章节标题"或文本末尾
        end_pat = r"^#{1,6}\s*第\s*[六6VI]\s*章|^#{1,6}\s*评标"
        s = re.search(start_pat, text, re.M)
        if not s:
            return (0, 0)  # 未找到，交由兜底
        e = re.search(end_pat, text[s.end():], re.M)
        if e: return (s.start(), s.end()+e.start())
        return (s.start(), len(text))

    def _extract_sections(self, block: str) -> List[str]:
        # 尝试从有序/无序列表中抽目录项，失败则返回 Canonical
        lines = block.splitlines()
        items = []
        bullet = re.compile(r"^\s*([0-9０-９一二三四五六七八九十]+[.)、])\s*(.+?)\s*$")
        
        for ln in lines:
            m = bullet.match(ln)
            if m:
                item = re.sub(r"（.*?）|\(.*?\)", "", m.group(2)).strip()
                item = re.sub(r"\s+", "", item)
                
                # 过滤掉装订要求等非章节内容
                if any(keyword in item for keyword in ["装订", "份数", "正本", "副本", "目录"]):
                    continue
                    
                if 2 <= len(item) <= 30:
                    items.append(item)
        
        # 过滤近义写法映射
        norm = []
        for x in items:
            if "方案" in x and "施工" in x: 
                norm.append("方案详细说明及施工组织设计")
            elif "偏差" in x: 
                norm.append("商务和技术偏差表")
            else: 
                norm.append(x)
        
        # 最终兜底
        dedup = []
        for x in norm:
            if x not in dedup: 
                dedup.append(x)
        
        return dedup or CANONICAL_SECTIONS

    def _render_skeleton(self, sections: List[str]) -> str:
        today = datetime.date.today().strftime("%Y-%m-%d")
        toc = "\n".join(f"{i+1}. {sec}" for i,sec in enumerate(sections))
        body = []
        for i, sec in enumerate(sections, 1):
            if sec == "方案详细说明及施工组织设计":
                hints = (
                    "> 评分对照提示：\n\n"
                    "> - 技术方案（25分）：项目理解、技术路线、关键设备参数、排放与能效保证值、系统集成、控制与数字化。\n\n"
                    "> - 施工方法及主要技术措施（25分）：组织机构、关键工序质量控制、干扰最小化与应急回退、安全文明与环保、试车与验收。\n\n"
                )
                body.append(f"## {self._num(i)}、{sec}\n{hints}> [占位]\n")
            else:
                body.append(f"## {self._num(i)}、{sec}\n> [占位]\n")
        return f"""---
 title: 投标文件（骨架）
 generated_at: {today}
 ---
 
 # 封面（模板）
 - 项目名称：{{PROJECT_NAME}}
 - 招标编号：{{TENDER_NO}}
 - 投标人：{{BIDDER_NAME}}（盖章）
 - 日期：{{YYYY}}年{{MM}}月{{DD}}日
 - 正/副本：正本1份，副本4份
 
 # 目 录
 {toc}
 
 ---
 
 {''.join(body)}
 
 ### 装订与份数提示
 - 正本/副本分别装订成册并编目录；避免可拆装订。
 """

    @staticmethod
    def _num(i:int)->str:
        CN="零一二三四五六七八九十"
        return CN[i] if i<11 else str(i)

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """同步执行方法，用于LangGraph工作流"""
        tender_path = state.get("tender_path")  # uploads/招标文件.md
        wiki_dir = state.get("wiki_dir", "wiki")
        pathlib.Path(wiki_dir).mkdir(parents=True, exist_ok=True)

        # 读取招标文件内容
        if not os.path.exists(tender_path):
            # 如果文件不存在，使用默认章节
            sections = CANONICAL_SECTIONS
            content = self._render_skeleton(sections)
        else:
            with open(tender_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            s, e = self._find_bid_format_block(text)
            sections = self._extract_sections(text[s:e]) if (s or e) else CANONICAL_SECTIONS
            content = self._render_skeleton(sections)

        out_path = os.path.join(wiki_dir, "投标文件_骨架.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        state["outline_path"] = out_path
        state["outline_sections"] = sections
        return state

    async def execute_async(self, context: Any) -> Any:
        """保持原有的异步接口兼容性"""
        # 从上传文件中获取招标文件内容
        uploaded_files = context.get("uploaded_files", [])
        if not uploaded_files:
            context["current_content"] = "未找到上传的招标文件"
            context["current_stage"] = "structure_analysis_error"
            return context
        
        # 假设第一个文件是招标文件
        tender_file = uploaded_files[0]
        text = tender_file.get("content", "")
        
        wiki_dir = "wiki"
        pathlib.Path(wiki_dir).mkdir(parents=True, exist_ok=True)

        s, e = self._find_bid_format_block(text)
        sections = self._extract_sections(text[s:e]) if (s or e) else CANONICAL_SECTIONS
        content = self._render_skeleton(sections)

        out_path = os.path.join(wiki_dir, "投标文件_骨架.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # 更新项目状态
        context["outline_path"] = out_path
        context["outline_sections"] = sections
        context["current_content"] = f"成功生成投标文件骨架，包含 {len(sections)} 个章节"
        context["current_stage"] = "structure_extraction_completed"
        
        return context