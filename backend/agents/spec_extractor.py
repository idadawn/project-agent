from typing import Dict, Any, Tuple
import re, os, pathlib, datetime
from .base import BaseAgent

class SpecExtractor(BaseAgent):
    def __init__(self):
        super().__init__("spec_extractor")
    
    def get_system_prompt(self) -> str:
        return """你是一个技术规格书分析专家。你的任务是从招标文件中精确提取第四章技术规格书的内容。"""

    START_PATS = [
        r"^#{1,6}\s*第\s*[四4IV]\s*章.*?(技术规格书|技术要求)",
    ]
    END_PATS = [
        r"^#{1,6}\s*第\s*[五5V]\s*章", r"^#{1,6}\s*投标文件格式"
    ]

    def _slice(self, text:str)->Tuple[int,int]:
        s = None
        for p in self.START_PATS:
            s = re.search(p, text, re.M)
            if s: break
        if not s: return (0,0)
        e = None
        for p in self.END_PATS:
            e = re.search(p, text[s.end():], re.M)
            if e: break
        if e: return (s.start(), s.end()+e.start())
        return (s.start(), len(text))

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """同步执行方法，用于LangGraph工作流"""
        tender_path = state.get("tender_path")
        wiki_dir = state.get("wiki_dir", "wiki")
        pathlib.Path(wiki_dir).mkdir(parents=True, exist_ok=True)

        # 读取招标文件内容
        if not os.path.exists(tender_path):
            # 如果文件不存在，使用默认内容
            payload = "# 第四章 技术规格书（未在文中定位，使用提纲占位）\n\n- 交钥匙范围\n- 技术参数与标准\n- 资料交付\n- 质量与验收\n- 安全与环保\n"
            spec_extracted = False
        else:
            with open(tender_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            s, e = self._slice(text)
            # 干运行：若抽不到，输出目录级提纲；正式运行可切换"全文保留"
            payload = text[s:e].strip() if (s or e) else "# 第四章 技术规格书（未在文中定位，使用提纲占位）\n\n- 交钥匙范围\n- 技术参数与标准\n- 资料交付\n- 质量与验收\n- 安全与环保\n"
            spec_extracted = bool(s or e)
        
        head = f"""---
title: 技术规格书（提取）
generated_at: {datetime.date.today().strftime("%Y-%m-%d")}
note: 由 SpecExtractor 自动抽取（从"第四章 技术规格书"至"第五章/投标文件格式"前）
---

"""
        
        out = os.path.join(wiki_dir, "技术规格书_提取.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(head + payload + "\n")
        
        state["spec_path"] = out
        state["spec_extracted"] = spec_extracted
        return state

    async def execute_async(self, context: Any) -> Any:
        """保持原有的异步接口兼容性"""
        uploaded_files = context.get("uploaded_files", [])
        if not uploaded_files:
            context["current_content"] = "未找到上传的招标文件"
            context["current_stage"] = "spec_extraction_error"
            return context
        
        tender_file = uploaded_files[0]
        text = tender_file.get("content", "")
        
        wiki_dir = "wiki"
        pathlib.Path(wiki_dir).mkdir(parents=True, exist_ok=True)

        s, e = self._slice(text)
        # 干运行：若抽不到，输出目录级提纲；正式运行可切换"全文保留"
        payload = text[s:e].strip() if (s or e) else "# 第四章 技术规格书（未在文中定位，使用提纲占位）\n\n- 交钥匙范围\n- 技术参数与标准\n- 资料交付\n- 质量与验收\n- 安全与环保\n"
        
        head = f"""---
title: 技术规格书（提取）
generated_at: {datetime.date.today().strftime("%Y-%m-%d")}
note: 由 SpecExtractor 自动抽取（从"第四章 技术规格书"至"第五章/投标文件格式"前）
---

"""
        
        out = os.path.join(wiki_dir, "技术规格书_提取.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(head + payload + "\n")
        
        # 更新项目状态
        context["spec_path"] = out
        context["spec_extracted"] = bool(s or e)
        context["current_content"] = f"成功提取技术规格书内容，{'已定位到具体章节' if (s or e) else '使用默认提纲'}"
        context["current_stage"] = "spec_extraction_completed"
        
        return context