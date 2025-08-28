from typing import Dict, Any, List
import os
from .base import BaseAgent, AgentContext, AgentResponse


class BidFormatAgent(BaseAgent):
    """专责：从招标文件中提取“第五章 投标文件格式”，并生成投标文件.md框架。"""

    def __init__(self):
        super().__init__("bid_format")

    def get_system_prompt(self) -> str:
        return """您是“投标文件格式”分析专家。请从招标文件中定位“第五章 投标文件格式”，并基于其目录结构生成“投标文件.md”框架（各章节占位）。

输出要求：
- 生成 Markdown 文件：投标文件/投标文件.md
- 每个章节以二级标题呈现，并给出“待补充”占位说明
- 在文末附上原始的“投标文件格式”节选（便于对照）
"""

    async def execute(self, context: AgentContext) -> AgentResponse:
        try:
            # 读取“第五章 投标文件格式”（仅该章原文，不含后续章节）
            format_text = self._load_bid_format_text()
            if not format_text:
                return AgentResponse(
                    content="未在招标文件中找到‘第五章 投标文件格式’。",
                    status="error",
                    metadata={"error": "bid_format_not_found"}
                )

            # 直接使用“投标文件格式”原文作为投标文件.md（保留原始目录与模板）
            content = format_text

            # 保存文件到 wiki 目录
            from backend.app_core.config import settings
            os.makedirs(settings.WIKI_DIR, exist_ok=True)
            proposal_path = os.path.join(settings.WIKI_DIR, "投标文件.md")
            with open(proposal_path, "w", encoding="utf-8") as f:
                f.write(content)

            return AgentResponse(
                content="已将‘第五章 投标文件格式’原文写入 wiki/投标文件.md。",
                status="completed",
                metadata={
                    "files_to_create": [
                        {
                            "name": "投标文件.md",
                            "content": content,
                            "type": "wiki",
                            "folder": "wiki",
                        }
                    ],
                    "generated_bid": {"path": proposal_path},
                    "stage": "bid_format_completed",
                    "current_agent": "bid_format",
                },
            )

        except Exception as e:
            return AgentResponse(
                content=f"投标文件框架生成失败: {str(e)}",
                status="error",
                metadata={"error": str(e)}
            )

    def _load_bid_format_text(self) -> str:
        """从 wiki/招标文件.md 精确截取‘第五章 投标文件格式’至下一章标题前的原文。"""
        # 回退：直接从wiki读取
        from backend.app_core.config import settings
        wiki_path = os.path.join(settings.WIKI_DIR, "招标文件.md")
        if os.path.exists(wiki_path):
            with open(wiki_path, "r", encoding="utf-8") as f:
                md_text = f.read()
            clean_text = md_text.replace("**", "")
            start = clean_text.find("第五章 投标文件格式")
            if start != -1:
                # 查找下一章标题，例如“第六章 ”或“第X章 ”
                import re
                next_chapter = re.search(r"\n第[一二三四五六七八九十百]+章\s+", clean_text[start+1:])
                if next_chapter:
                    end = start + 1 + next_chapter.start()
                    return clean_text[start:end].rstrip() + "\n"
                return clean_text[start:]
        return ""

    # 不再渲染框架，直接使用原文


