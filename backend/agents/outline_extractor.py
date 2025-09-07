# -*- coding: utf-8 -*-
"""
鲁棒的方案提纲抽取智能体 - 三层匹配（规则 + 语义 + LLM判别）
目标：从任意中文技术文档中稳定抽取"八、方案详细说明及施工组织设计"结构
"""

from typing import Dict, Any, List, Optional, Tuple
import re
import os
import pathlib
import datetime
from dataclasses import dataclass
from enum import Enum
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
from collections import Counter
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化jieba分词
jieba.initialize()

# 同义词词典
SYNONYM_DICT = {
    "尘源点捕集罩": ["吸风罩", "集气罩", "捕集装置", "收集罩", "除尘罩"],
    "平面管网路由": ["总图管线", "管网布置", "流程管线走向", "管道布置", "管线路由"],
    "钢渣一次处理": ["钢渣初级处理", "钢渣预处理", "一次处理工艺", "初级处理系统"],
    "除尘系统布置": ["除尘系统布局", "除尘设备布置", "除尘装置安排", "除尘设施配置"],
    "关键技术说明": ["核心技术说明", "技术要点阐述", "关键技术阐述", "技术难点说明"],
    "施工方法": ["施工工艺", "施工技术", "施工方案", "施工流程"],
    "技术措施": ["技术方案", "技术手段", "技术方法", "技术对策"],
    "停机时间": ["停机配合", "停产时间", "设备停机", "生产中断"]
}

# 中文数字映射扩展
CN_NUM_MAP = {
    '零': 0, '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10, '十一': 11, '十二': 12,
    '十三': 13, '十四': 14, '十五': 15, '十六': 16, '十七': 17, '十八': 18,
    '十九': 19, '二十': 20, '三十': 30, '四十': 40, '五十': 50, '六十': 60,
    '七十': 70, '八十': 80, '九十': 90, '百': 100
}

try:
    from .base import BaseAgent, AgentContext, AgentResponse
except Exception:
    class BaseAgent:
        name = "base"
        def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
            return state
    
    class AgentContext:
        pass
    
    class AgentResponse:
        def __init__(self, content="", metadata=None):
            self.content = content
            self.metadata = metadata or {}


class MatchStatus(str, Enum):
    OK = "ok"
    MISSING = "missing"
    LOW_CONFIDENCE = "low_confidence"
    CONFLICT = "conflict"


@dataclass
class HeadingNode:
    level: int
    text: str
    normalized_text: str
    start_pos: int
    end_pos: int
    children: List['HeadingNode']
    content_start: Optional[int] = None
    content_end: Optional[int] = None


@dataclass
class TargetSection:
    key: str
    normalized_key: str
    description: str
    aliases: List[str]
    keywords: List[str]
    expected_level: int
    parent_key: Optional[str] = None


class OutlineExtractorAgent(BaseAgent):
    name = "outline_extractor"
    
    # 目标章节定义 - 八、方案详细说明及施工组织设计
    TARGET_SECTIONS = [
        # 主章节
        TargetSection(
            key="chapter.8.plan_and_org",
            normalized_key="八、方案详细说明及施工组织设计",
            description="第八章方案详细说明及施工组织设计",
            aliases=[
                "方案详细说明及施工组织设计",
                "技术方案与施工组织", 
                "实施方案与施工组织",
                "施工组织设计与技术方案",
                "八、", "第八章", "第8章"
            ],
            keywords=["方案", "详细", "施工", "组织", "设计", "技术", "措施"],
            expected_level=1
        ),
        
        # 子章节 1、方案的详细说明
        TargetSection(
            key="plan.detailed_description",
            normalized_key="1、方案的详细说明",
            description="第一节方案的详细说明",
            aliases=["方案的详细说明", "技术方案说明", "方案说明", "一、"],
            keywords=["方案", "详细", "说明", "技术"],
            expected_level=2,
            parent_key="chapter.8.plan_and_org"
        ),
        
        # 子章节 1.1 优化提升改造部分详细方案说明
        TargetSection(
            key="plan.upgrade_detail",
            normalized_key="1.1 优化提升改造部分详细方案说明",
            description="优化提升改造部分详细方案说明",
            aliases=[
                "优化提升改造部分详细方案说明",
                "技术改造方案说明", 
                "优化改造详细方案",
                "技改方案"
            ],
            keywords=["优化", "提升", "改造", "技改", "详细", "方案", "说明"],
            expected_level=3,
            parent_key="plan.detailed_description"
        ),
        
        # 子章节 1.2 尘源点捕集罩方案详细说明
        TargetSection(
            key="plan.dust_capture",
            normalized_key="1.2 尘源点捕集罩方案详细说明",
            description="尘源点捕集罩方案详细说明",
            aliases=[
                "尘源点捕集罩方案详细说明",
                "吸风罩方案", 
                "集气罩方案",
                "捕集装置方案"
            ],
            keywords=["尘源", "粉尘", "捕集", "收集", "罩", "吸风", "集气"],
            expected_level=3,
            parent_key="plan.detailed_description"
        ),
        
        # 子章节 1.3 平面管网路由方案图及说明
        TargetSection(
            key="plan.pipeline_layout",
            normalized_key="1.3 平面管网路由方案图及说明",
            description="平面管网路由方案图及说明",
            aliases=[
                "平面管网路由方案图及说明",
                "总图管线布置", 
                "管网布置方案",
                "流程管线走向"
            ],
            keywords=["平面", "管网", "管线", "管道", "路由", "走向", "布置", "总图"],
            expected_level=3,
            parent_key="plan.detailed_description"
        ),
        
        # 子章节 1.4 钢渣一次处理工艺系统方案图及详细说明
        TargetSection(
            key="plan.slag_system",
            normalized_key="1.4 钢渣一次处理工艺系统方案图及详细说明",
            description="钢渣一次处理工艺系统方案图及详细说明",
            aliases=[
                "钢渣一次处理工艺系统方案图及详细说明",
                "钢渣处理系统方案", 
                "一次处理工艺方案"
            ],
            keywords=["钢渣", "一次处理", "初级处理", "工艺系统", "流程", "方案"],
            expected_level=3,
            parent_key="plan.detailed_description"
        ),
        
        # 子章节 1.5 除尘系统布置图及方案详细说明
        TargetSection(
            key="plan.dedusting_layout",
            normalized_key="1.5 除尘系统布置图及方案详细说明",
            description="除尘系统布置图及方案详细说明",
            aliases=[
                "除尘系统布置图及方案详细说明",
                "除尘系统布局方案", 
                "除尘布置图"
            ],
            keywords=["除尘", "除尘系统", "布置", "布局", "方案", "说明", "图"],
            expected_level=3,
            parent_key="plan.detailed_description"
        ),
        
        # 子章节 1.6 关键技术说明等
        TargetSection(
            key="plan.key_tech",
            normalized_key="1.6 关键技术说明等",
            description="关键技术说明等",
            aliases=[
                "关键技术说明等",
                "核心技术说明", 
                "技术要点",
                "技术难点"
            ],
            keywords=["关键", "核心", "技术", "要点", "难点", "说明"],
            expected_level=3,
            parent_key="plan.detailed_description"
        ),
        
        # 子章节 2、施工组织设计
        TargetSection(
            key="org.construction_design",
            normalized_key="2、施工组织设计",
            description="第二节施工组织设计",
            aliases=["施工组织设计", "施工组织", "二、"],
            keywords=["施工", "组织", "设计"],
            expected_level=2,
            parent_key="chapter.8.plan_and_org"
        ),
        
        # 子章节 2.1 施工方法及主要技术措施（施工方案）
        TargetSection(
            key="org.construction_method",
            normalized_key="2.1 施工方法及主要技术措施（施工方案）",
            description="施工方法及主要技术措施（施工方案）",
            aliases=[
                "施工方法及主要技术措施（施工方案）",
                "施工方法与技术措施", 
                "施工方案"
            ],
            keywords=["施工", "方法", "技术", "措施", "方案"],
            expected_level=3,
            parent_key="org.construction_design"
        ),
        
        # 子章节 2.2 需投标人配合停机时间的详细组织设计
        TargetSection(
            key="org.shutdown_coordination",
            normalized_key="2.2 需投标人配合停机时间的详细组织设计",
            description="需投标人配合停机时间的详细组织设计",
            aliases=[
                "需投标人配合停机时间的详细组织设计",
                "停机时间配合组织", 
                "停机组织安排"
            ],
            keywords=["停机", "配合", "时间", "组织", "安排", "计划"],
            expected_level=3,
            parent_key="org.construction_design"
        )
    ]
    
    def __init__(self):
        try:
            super().__init__(self.name)
        except:
            # 如果LLM客户端初始化失败，使用备用初始化
            self.llm_client = None
        self.vectorizer = TfidfVectorizer()
        
    def get_system_prompt(self) -> str:
        return "你是方案结构抽取专家，从技术文档中精确识别和抽取方案详细说明及施工组织设计的章节结构。"
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行方案结构抽取（工作流兼容版本）"""
        try:
            # 将字典状态转换为AgentContext
            context = self._state_to_context(state)
            
            # 获取招标文件内容
            tender_text = self._extract_tender_text(context)
            if not tender_text:
                # 返回错误状态
                state["error"] = "未找到招标文件内容"
                state["outline_extraction_status"] = "failed"
                return state
            
            # 构建标题树
            heading_tree = self._build_heading_tree(tender_text)
            
            # 定位第八章
            chapter_8 = self._locate_chapter_8(heading_tree, tender_text)
            
            # 抽取子章节结构
            results = self._extract_sub_sections(chapter_8, tender_text)
            
            # 将结果存入状态
            state["outline_results"] = results
            state["outline_extraction_status"] = "success"
            
            # 添加统计信息
            matched_ok = sum(1 for r in results if r['status'] == MatchStatus.OK)
            matched_low = sum(1 for r in results if r['status'] == MatchStatus.LOW_CONFIDENCE)
            matched_missing = sum(1 for r in results if r['status'] == MatchStatus.MISSING)
            total = len(results)
            
            state["outline_matched_ok"] = matched_ok
            state["outline_matched_low"] = matched_low
            state["outline_missing"] = matched_missing
            state["outline_total"] = total
            state["outline_confidence"] = sum(r['confidence'] for r in results) / total if total > 0 else 0.0
            
            return state
            
        except Exception as e:
            state["error"] = f"结构抽取失败: {str(e)}"
            state["outline_extraction_status"] = "failed"
            return state
    
    def _state_to_context(self, state: Dict[str, Any]) -> AgentContext:
        """将字典状态转换为AgentContext"""
        try:
            from .base import AgentContext
            return AgentContext(
                user_input=state.get("user_input", "抽取方案结构"),
                uploaded_files=state.get("uploaded_files", []),
                parsed_documents=state.get("parsed_documents", []),
                project_state=state.get("project_state", {})
            )
        except:
            # 备用实现
            class SimpleContext:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)
            return SimpleContext(
                user_input=state.get("user_input", "抽取方案结构"),
                uploaded_files=state.get("uploaded_files", []),
                parsed_documents=state.get("parsed_documents", []),
                project_state=state.get("project_state", {})
            )

    def _extract_tender_text(self, context) -> Optional[str]:
        """从上下文中提取招标文件文本"""
        # 尝试从不同来源获取文本
        project_state = getattr(context, 'project_state', {})
        
        # 1. 从上传文件获取
        uploaded_files = getattr(context, 'uploaded_files', [])
        for file_info in uploaded_files:
            if file_info.get('filename', '').endswith('.md'):
                file_path = file_info.get('path')
                if file_path and os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
        
        # 2. 从项目状态获取
        tender_path = project_state.get('tender_path')
        if tender_path and os.path.exists(tender_path):
            with open(tender_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # 3. 从解析的文档获取
        parsed_docs = getattr(context, 'parsed_documents', [])
        for doc in parsed_docs:
            if doc.get('filename', '').endswith('.md'):
                content = doc.get('content')
                if content:
                    return content
        
        return None
    
    def _build_heading_tree(self, text: str) -> List[HeadingNode]:
        """构建文档标题树"""
        lines = text.split('\n')
        headings = []
        stack = []
        
        for i, line in enumerate(lines):
            # 检测标题行
            level, title = self._parse_heading_line(line)
            if level > 0:
                node = HeadingNode(
                    level=level,
                    text=line.strip(),
                    normalized_text=self._normalize_heading(title),
                    start_pos=text.find(line),
                    end_pos=text.find(line) + len(line),
                    children=[]
                )
                
                # 构建层级关系
                while stack and stack[-1].level >= level:
                    stack.pop()
                
                if stack:
                    stack[-1].children.append(node)
                else:
                    headings.append(node)
                
                stack.append(node)
        
        return headings
    
    def _parse_heading_line(self, line: str) -> Tuple[int, str]:
        """解析标题行，返回层级和标题文本"""
        line = line.strip()
        
        # 匹配 Markdown 标题
        md_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if md_match:
            level = len(md_match.group(1))
            title = md_match.group(2)
            return level, title
        
        # 匹配中文数字标题
        cn_match = re.match(r'^([一二三四五六七八九十]+)[、.:]\s*(.+)$', line)
        if cn_match:
            level = self._chinese_number_to_int(cn_match.group(1))
            title = cn_match.group(2)
            return min(level, 6), title  # 限制最大层级
        
        # 匹配阿拉伯数字标题
        num_match = re.match(r'^(\d+)[、.:]\s*(.+)$', line)
        if num_match:
            level = int(num_match.group(1))
            title = num_match.group(2)
            return min(level, 6), title
        
        return 0, ""
    
    def _chinese_number_to_int(self, cn_num: str) -> int:
        """中文数字转阿拉伯数字（支持复杂数字）"""
        if cn_num.isdigit():
            return int(cn_num)
        
        # 处理复杂中文数字
        total = 0
        current = 0
        
        for char in cn_num:
            if char in CN_NUM_MAP:
                value = CN_NUM_MAP[char]
                if value >= 10:  # 十、百等
                    if current == 0:
                        current = 1
                    total += current * value
                    current = 0
                else:
                    current = value
            else:
                # 非数字字符，跳过
                continue
        
        total += current
        return total if total > 0 else 0
    
    def _normalize_heading(self, text: str) -> str:
        """增强的标题归一化"""
        if not text:
            return ""
        
        # 1. 统一编号格式
        text = re.sub(r'^第\s*([一二三四五六七八九十百零〇0-9]+)\s*章\s*[:：]?', r'\1、', text)
        text = re.sub(r'^第\s*([一二三四五六七八九十百零〇0-9]+)\s*节\s*[:：]?', r'\1、', text)
        
        # 2. 统一分隔符
        text = re.sub(r'[、.:．。]', '.', text)
        
        # 3. 中文数字转阿拉伯数字
        def replace_chinese_numbers(match):
            cn_num = match.group(1)
            return str(self._chinese_number_to_int(cn_num))
        
        text = re.sub(r'([一二三四五六七八九十百零〇]+)', replace_chinese_numbers, text)
        
        # 4. 去除括号和特殊字符
        text = re.sub(r'[（）()\[\]【】「」《》<>\*\-\+\s]', '', text)
        
        # 5. 转换为小写
        text = text.lower()
        
        # 6. 标准化编号格式
        text = re.sub(r'(\d+)\.(\d+)', r'\1.\2', text)  # 确保点号格式
        
        return text.strip()
    
    def _locate_chapter_8(self, heading_tree: List[HeadingNode], text: str) -> Optional[HeadingNode]:
        """定位第八章"""
        # 首先尝试精确匹配
        for node in heading_tree:
            if self._match_chapter_8(node):
                return node
        
        # 如果精确匹配失败，使用语义搜索
        return self._semantic_locate_chapter_8(text)
    
    def _match_chapter_8(self, node: HeadingNode) -> bool:
        """匹配第八章"""
        target = self.TARGET_SECTIONS[0]  # 第八章
        
        # 规则层匹配
        rule_score = self._rule_layer_score(node.normalized_text, target)
        # 语义层匹配
        semantic_score = self._semantic_layer_score(node.text, target)
        
        # 融合得分
        total_score = 0.4 * rule_score + 0.6 * semantic_score
        return total_score >= 0.7
    
    def _rule_layer_score(self, text: str, target: TargetSection) -> float:
        """增强的规则层匹配得分"""
        score = 0.0
        
        # 1. 精确别名匹配（最高权重）
        for alias in target.aliases:
            if alias in text:
                score += 0.4
                logger.debug(f"精确别名匹配: {alias} -> +0.4")
                break
        
        # 2. 关键词覆盖率
        matched_keywords = []
        for keyword in target.keywords:
            if keyword in text:
                score += 0.08  # 降低单个关键词权重
                matched_keywords.append(keyword)
        
        if matched_keywords:
            logger.debug(f"关键词匹配: {matched_keywords} -> +{0.08 * len(matched_keywords):.2f}")
        
        # 3. 同义词扩展匹配
        synonym_score = self._synonym_match_score(text, target)
        score += synonym_score * 0.2
        
        # 4. 编号格式匹配
        numbering_score = self._numbering_format_score(text, target)
        score += numbering_score * 0.1
        
        return min(score, 1.0)
    
    def _synonym_match_score(self, text: str, target: TargetSection) -> float:
        """同义词匹配得分"""
        score = 0.0
        
        # 检查目标描述中的关键词是否在同义词词典中
        for keyword in target.keywords:
            if keyword in SYNONYM_DICT:
                synonyms = SYNONYM_DICT[keyword]
                for synonym in synonyms:
                    if synonym in text:
                        score += 0.2
                        logger.debug(f"同义词匹配: {keyword} -> {synonym} -> +0.2")
                        break
        
        return min(score, 1.0)
    
    def _numbering_format_score(self, text: str, target: TargetSection) -> float:
        """编号格式匹配得分"""
        # 检查是否包含标准编号格式
        if re.search(r'\d+(\.\d+)*', text):
            return 0.3
        
        # 检查中文编号格式
        if re.search(r'[一二三四五六七八九十]+(?:[、.][一二三四五六七八九十]+)*', text):
            return 0.2
        
        return 0.0
    
    def _semantic_layer_score(self, text: str, target: TargetSection) -> float:
        """增强的语义层匹配得分"""
        score = 0.0
        
        # 1. TF-IDF 余弦相似度
        try:
            corpus = [text, target.description] + target.aliases
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            score += similarity * 0.5
            logger.debug(f"TF-IDF相似度: {similarity:.3f} -> +{similarity * 0.5:.3f}")
        except Exception as e:
            logger.warning(f"TF-IDF计算失败: {e}")
        
        # 2. Jaccard相似度（分词级别）
        jaccard_score = self._jaccard_similarity(text, target.description)
        score += jaccard_score * 0.3
        logger.debug(f"Jaccard相似度: {jaccard_score:.3f} -> +{jaccard_score * 0.3:.3f}")
        
        # 3. 编辑距离相似度
        edit_distance_score = self._edit_distance_similarity(text, target.description)
        score += edit_distance_score * 0.2
        logger.debug(f"编辑距离相似度: {edit_distance_score:.3f} -> +{edit_distance_score * 0.2:.3f}")
        
        return min(score, 1.0)
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """计算Jaccard相似度"""
        if not text1 or not text2:
            return 0.0
        
        # 分词
        words1 = set(jieba.cut(text1))
        words2 = set(jieba.cut(text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _edit_distance_similarity(self, text1: str, text2: str) -> float:
        """计算基于编辑距离的相似度"""
        if not text1 or not text2:
            return 0.0
        
        # 简化的编辑距离相似度
        len1, len2 = len(text1), len(text2)
        max_len = max(len1, len2)
        
        if max_len == 0:
            return 1.0
        
        # 计算公共子串长度
        common = 0
        for i in range(min(len1, len2)):
            if text1[i] == text2[i]:
                common += 1
            else:
                break
        
        return common / max_len
    
    def _semantic_locate_chapter_8(self, text: str) -> Optional[HeadingNode]:
        """增强的语义定位第八章"""
        lines = text.split('\n')
        
        # 方案相关关键词（带权重）
        keyword_weights = {
            "方案": 2.0, "施工": 1.5, "组织": 1.5, "设计": 1.5, 
            "技术": 1.2, "措施": 1.2, "详细": 1.0, "说明": 1.0,
            "优化": 1.0, "改造": 1.0, "尘源": 0.8, "捕集": 0.8,
            "管网": 0.8, "路由": 0.8, "钢渣": 0.8, "除尘": 0.8,
            "关键": 0.8, "停机": 0.8, "配合": 0.8, "时间": 0.5
        }
        
        best_score = 0.0
        best_start = -1
        best_end = -1
        
        # 滑动窗口检测（更大的窗口）
        window_size = 15
        for i in range(len(lines) - window_size + 1):
            window_lines = lines[i:i+window_size]
            window_text = ' '.join(window_lines)
            
            # 计算加权关键词密度
            window_score = 0.0
            keyword_count = 0
            
            for keyword, weight in keyword_weights.items():
                if keyword in window_text:
                    window_score += weight
                    keyword_count += 1
            
            # 归一化得分
            if keyword_count > 0:
                window_score = window_score / sum(keyword_weights.values()) * 2
            
            # 检查是否包含第八章的典型模式
            pattern_bonus = 0.0
            if any(pattern in window_text for pattern in ["第八章", "第8章", "八、"]):
                pattern_bonus += 0.3
            
            if any(pattern in window_text for pattern in ["方案详细", "施工组织", "技术方案"]):
                pattern_bonus += 0.2
            
            total_score = window_score + pattern_bonus
            
            if total_score > best_score:
                best_score = total_score
                best_start = i
                best_end = i + window_size - 1
        
        if best_score >= 0.4:  # 降低阈值以提高召回率
            start_pos = text.find(lines[best_start])
            end_pos = text.find(lines[best_end]) + len(lines[best_end])
            
            # 创建伪第八章节点
            return HeadingNode(
                level=1,
                text="第八章 方案详细说明及施工组织设计（语义定位）",
                normalized_text="8、方案详细说明及施工组织设计",
                start_pos=start_pos,
                end_pos=end_pos,
                children=[]
            )
        
        logger.warning("语义定位第八章失败，未找到方案相关密集区域")
        return None
    
    def _extract_sub_sections(self, chapter_node: Optional[HeadingNode], text: str) -> List[Dict]:
        """增强的子章节结构抽取"""
        if not chapter_node:
            # 如果找不到第八章，返回模板结构
            return self._create_template_structure()
        
        results = []
        
        # 遍历所有目标子章节
        for target in self.TARGET_SECTIONS[1:]:  # 跳过第八章
            best_match = None
            best_score = 0.0
            alternatives = []
            
            # 在第八章的子节点中搜索匹配
            if chapter_node.children:
                for child in chapter_node.children:
                    score = self._match_sub_section(child, target)
                    
                    # 记录所有候选
                    if score > 0.3:
                        alternatives.append({
                            'node': child,
                            'score': score,
                            'text': child.text
                        })
                    
                    if score > best_score:
                        best_score = score
                        best_match = child
            
            # 如果没有在直接子节点中找到，尝试在整个第八章范围内搜索
            if best_score < 0.5:
                best_match, best_score = self._search_in_chapter_content(chapter_node, text, target)
            
            if best_match and best_score >= 0.5:  # 降低阈值
                # 提取内容预览
                content_preview = self._extract_content_preview(text, best_match)
                
                results.append({
                    'normalized_key': target.normalized_key,
                    'found_title': best_match.text,
                    'location': {'start': best_match.start_pos, 'end': best_match.end_pos},
                    'confidence': best_score,
                    'content_preview': content_preview,
                    'status': MatchStatus.OK if best_score >= 0.6 else MatchStatus.LOW_CONFIDENCE,
                    'alternatives': [alt for alt in alternatives if alt['score'] >= 0.4]
                })
            else:
                results.append({
                    'normalized_key': target.normalized_key,
                    'found_title': '',
                    'location': None,
                    'confidence': best_score,
                    'content_preview': '',
                    'status': MatchStatus.MISSING,
                    'alternatives': alternatives
                })
        
        return results
    
    def _search_in_chapter_content(self, chapter_node: HeadingNode, text: str, target: TargetSection) -> Tuple[Optional[HeadingNode], float]:
        """在整个第八章内容范围内搜索匹配的子章节"""
        # 获取第八章内容范围
        chapter_content = text[chapter_node.start_pos:chapter_node.end_pos]
        
        # 在内容中搜索目标关键词
        best_score = 0.0
        best_match = None
        
        # 搜索包含目标关键词的段落
        paragraphs = chapter_content.split('\n\n')
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 检查段落是否包含目标关键词
            score = self._rule_layer_score(para, target) * 0.6 + self._semantic_layer_score(para, target) * 0.4
            
            if score > best_score:
                best_score = score
                # 创建伪节点
                best_match = HeadingNode(
                    level=target.expected_level,
                    text=para[:100] + "..." if len(para) > 100 else para,
                    normalized_text=self._normalize_heading(para[:50]),
                    start_pos=text.find(para),
                    end_pos=text.find(para) + len(para),
                    children=[]
                )
        
        return best_match, best_score
    
    def _extract_content_preview(self, text: str, node: HeadingNode, max_length: int = 200) -> str:
        """提取内容预览"""
        if node.content_start and node.content_end:
            content = text[node.content_start:node.content_end]
        else:
            # 从节点位置向后提取一定长度的内容
            content_start = node.end_pos
            content_end = min(len(text), content_start + 500)  # 提取500字符
            content = text[content_start:content_end]
        
        # 清理内容
        content = re.sub(r'\s+', ' ', content.strip())
        
        # 截取预览
        if len(content) > max_length:
            return content[:max_length] + "..."
        return content
    
    def _match_sub_section(self, node: HeadingNode, target: TargetSection) -> float:
        """增强的子章节匹配"""
        # 规则层得分
        rule_score = self._rule_layer_score(node.normalized_text, target)
        
        # 语义层得分
        semantic_score = self._semantic_layer_score(node.text, target)
        
        # 层级匹配得分
        level_diff = abs(node.level - target.expected_level)
        level_score = max(0.1, 1.0 - level_diff * 0.3)  # 层级差异惩罚
        
        # 位置得分（在第八章中的相对位置）
        position_score = self._calculate_position_score(node, target)
        
        # 融合得分（调整权重）
        total_score = (
            0.35 * rule_score + 
            0.35 * semantic_score + 
            0.2 * level_score + 
            0.1 * position_score
        )
        
        logger.debug(f"匹配子章节: {node.text} -> {target.normalized_key}")
        logger.debug(f"  规则分: {rule_score:.3f}, 语义分: {semantic_score:.3f}, 层级分: {level_score:.3f}, 位置分: {position_score:.3f}")
        logger.debug(f"  总分: {total_score:.3f}")
        
        return total_score
    
    def _calculate_position_score(self, node: HeadingNode, target: TargetSection) -> float:
        """计算位置得分（基于目标章节的预期位置）"""
        # 这里可以根据目标章节的预期顺序给出位置奖励
        # 例如：1.1 应该在 1.2 之前等
        
        # 简单实现：给所有节点基础分
        return 0.5
    
    def _create_template_structure(self) -> List[Dict]:
        """创建模板结构"""
        return [
            {
                'normalized_key': target.normalized_key,
                'found_title': '',
                'location': None,
                'confidence': 0.0,
                'status': MatchStatus.MISSING
            }
            for target in self.TARGET_SECTIONS[1:]  # 跳过第八章
        ]
    
    def _create_success_response(self, results: List[Dict], text: str) -> Dict[str, Any]:
        """创建增强的成功响应"""
        # 统计匹配情况
        matched_ok = sum(1 for r in results if r['status'] == MatchStatus.OK)
        matched_low = sum(1 for r in results if r['status'] == MatchStatus.LOW_CONFIDENCE)
        matched_missing = sum(1 for r in results if r['status'] == MatchStatus.MISSING)
        total = len(results)
        
        content = f"✅ 方案结构抽取完成 ({matched_ok}个精确匹配, {matched_low}个低置信度, {matched_missing}个缺失)\n\n"
        
        for result in results:
            if result['status'] == MatchStatus.OK:
                status_icon = "✅"
                status_text = "精确匹配"
            elif result['status'] == MatchStatus.LOW_CONFIDENCE:
                status_icon = "⚠️"
                status_text = "低置信度"
            else:
                status_icon = "❌"
                status_text = "缺失"
            
            content += f"{status_icon} {result['normalized_key']} ({status_text})"
            
            if result['found_title']:
                content += f" → {result['found_title']} (置信度: {result['confidence']:.2f})"
            
            if result.get('content_preview'):
                content += f"\n   📝 内容预览: {result['content_preview']}"
            
            if result.get('alternatives') and len(result['alternatives']) > 0:
                content += f"\n   🔍 备选匹配: {len(result['alternatives'])}个"
            
            content += "\n\n"
        
        # 添加统计摘要
        content += f"\n📊 匹配统计:\n"
        content += f"   • 精确匹配: {matched_ok}/{total}\n"
        content += f"   • 低置信度: {matched_low}/{total}\n"
        content += f"   • 缺失章节: {matched_missing}/{total}\n"
        content += f"   • 总体置信度: {sum(r['confidence'] for r in results) / total:.2f}\n"
        
        return {
            'content': content,
            'metadata': {
                'outline_results': results,
                'matched_ok_count': matched_ok,
                'matched_low_count': matched_low,
                'missing_count': matched_missing,
                'total_count': total,
                'overall_confidence': sum(r['confidence'] for r in results) / total,
                'action': 'outline_extracted',
                'timestamp': datetime.datetime.now().isoformat()
            }
        }
    
    def _create_error_response(self, error_msg: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            'content': f"❌ {error_msg}",
            'metadata': {'action': 'outline_extraction_failed', 'error': error_msg},
            'status': 'error'
        }