# backend/agents/spec_extractor.py
from typing import Dict, Any
import os, re, pathlib, datetime
from utils.extract_bid_section import extract_tech_spec_section

try:
    from .base import BaseAgent
except Exception:
    class BaseAgent:
        name = "base"
        def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
            return state

class SpecExtractor(BaseAgent):
    name = "spec_extractor"

    def __init__(self):
        try:
            super().__init__(self.name)
        except TypeError:
            # Fallback for when base class doesn't expect parameters
            pass

    def get_system_prompt(self) -> str:
        return "你是技术规格书提取专家，从招标文件中精确提取技术要求和规格书内容。"

        from utils.extract_bid_section import extract_tech_spec_section
>>>>>>> c9213e8 (修改部分流程)
        section = extract_tech_spec_section(text, include_heading=True)
    def _slice(self, text: str):
        """优先使用通用状态机；失败再用旧模式回退切片。"""
        section = extract_tech_spec_section(text, include_heading=True)
=======
        from utils.extract_bid_section import extract_tech_spec_section
>>>>>>> c9213e8 (修改部分流程)
        section = extract_tech_spec_section(text, include_heading=True)
        if section:
            # 返回切片位置以兼容后续逻辑（仅内部使用，外部直接写入 section）
            start = text.find(section.split("\n", 1)[0])
            end = start + len(section) if start >= 0 else None
            return start, end
        # 旧回退：原有正则法
        patterns = [
            r"第四章[\s]*技术规格书",
            r"第四章[\s]*技术要求",
            r"第四章[\s]*技术规范",
            r"第四章[\s]*技术标准",
            r"四、[\s]*技术规格书",
            r"四、[\s]*技术要求",
            r"4[\s]*技术规格书",
            r"4[\s]*技术要求",
            r"第4章[\s]*技术规格书",
            r"第4章[\s]*技术要求"
        ]
        start = None
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start = match.start()
                break
        if start is None:
            return None, None
        end_patterns = [
            r"第五章",
            r"第五章[\s]*投标文件格式",
            r"第五章[\s]*招标文件格式",
            r"五、",
            r"5[\s]*",
            r"投标文件格式",
            r"招标文件格式",
            r"第5章",
            r"第六章",
            r"第6章"
        ]
        end = None
        for pattern in end_patterns:
            match = re.search(pattern, text[start:], re.IGNORECASE)
            if match:
                end = start + match.start()
                break
        return start, end

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # ✅ 统一用传入的 tender_path，不要再拼 uploads/
        tender_path = self._get_tender_path(state)
        wiki_dir = state.get("wiki_dir", "wiki")
        pathlib.Path(wiki_dir).mkdir(parents=True, exist_ok=True)

        with open(tender_path, "r", encoding="utf-8") as f:
            text = f.read()
        s,e = self._slice(text)
        extracted = False
        if s is not None and e is not None and s >= 0:
            payload = text[s:e].strip()
            extracted = True
            from utils.extract_bid_section import extract_tech_spec_section
>>>>>>> c9213e8 (修改部分流程)
            direct = extract_tech_spec_section(text, include_heading=True)
        else:
            # 再尝试直接拿状态机文本（避免切片定位失败，但已抽到文本的情况）
            direct = extract_tech_spec_section(text, include_heading=True)
=======
            from utils.extract_bid_section import extract_tech_spec_section
>>>>>>> c9213e8 (修改部分流程)
            direct = extract_tech_spec_section(text, include_heading=True)
            if direct:
                payload = direct.strip()
                extracted = True
            else:
                payload = (
                    "# 第四章 技术规格书（未在文中定位，使用提纲占位）\n\n"
                    "- 交钥匙范围\n- 技术参数与标准\n- 资料交付\n- 质量与验收\n- 安全与环保\n"
                )
        head = f"""---
title: 技术规格书（提取）
generated_at: {datetime.date.today().strftime("%Y-%m-%d")}
note: 由 SpecExtractor 自动抽取（从"第四章 技术规格书/技术要求"至"第五章/投标文件格式"前）
---

"""
        out = os.path.join(wiki_dir, "技术规格书_提取.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(head+payload+"\n")
        state["spec_path"] = out
        state["spec_extracted"] = bool(extracted)
        return state
    
    def _get_tender_path(self, state: Dict[str, Any]) -> str:
        """统一解析招标文件路径"""
        from pathlib import Path
        
        # 1) 优先：传入的 tender_path
        p = state.get("tender_path")
        if p and Path(p).exists():
            return str(Path(p).resolve())
        
        # 2) 次优：从 meta 中获取
        meta = state.get("meta", {})
        p = meta.get("tender_path")
        if p and Path(p).exists():
            return str(Path(p).resolve())
        
        # 3) 次优：兼容路径
        p = meta.get("legacy_tender_path")
        if p and Path(p).exists():
            return str(Path(p).resolve())
        
        # 4) 占底：常见目录候选
        for candidate in [
            Path("uploads") / "招标文件.md",
            Path("/root/project/git/project-agent/uploads") / "招标文件.md",
            Path("wiki") / "招标文件.md",
            Path("/root/project/git/project-agent/wiki") / "招标文件.md",
        ]:
            if candidate.exists():
                return str(candidate.resolve())
        
        raise FileNotFoundError("未找到招标文件：tender_path/meta/legacy/candidates 均不存在")