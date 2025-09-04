# -*- coding: utf-8 -*-
"""
从招标文件中提取方案提纲结构，生成通用提案大纲
支持从"方案详细说明及施工组织设计"等章节提取结构
"""

import re
from typing import List, Dict, Optional
import os


def extract_proposal_outline(text: str, outline_sections: List[str] = None) -> Dict[str, List[str]]:
    """
    从招标文件文本中提取方案提纲结构
    
    Args:
        text: 招标文件完整文本
        outline_sections: 从招标文件骨架中提取的章节列表（可选）
        
    Returns:
        包含方案提纲结构的字典，包含主要章节和子章节
    """
    
    outline = {"main_sections": [], "sub_sections": {}}
    
    # 首先尝试从招标文件骨架中提取的方案章节
    if outline_sections:
        proposal_section = _find_proposal_section_in_outline(outline_sections)
        if proposal_section:
            # 从完整文本中提取该方案章节的详细内容
            section_content = _extract_specific_section_content(text, proposal_section)
            if section_content:
                # 解析章节结构
                sections = _parse_section_structure(section_content)
                outline["main_sections"] = sections.get("main", [])
                outline["sub_sections"] = sections.get("sub", {})
                return outline
    
    # 如果没有从骨架中找到，尝试直接文本搜索投标文件格式章节
    # 查找"第五章 投标文件格式"或类似章节
    bid_format_patterns = [
        r"第[五5]章[\s\S]*?投标文件格式",
        r"投标文件格式",
        r"第五章[\s\S]*?格式",
        r"第5章[\s\S]*?格式"
    ]
    
    for pattern in bid_format_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start_pos = match.start()
            # 提取投标文件格式章节内容
            section_content = _extract_bid_format_section_content(text, start_pos)
            if section_content:
                # 从投标文件格式中提取方案相关子章节
                proposal_subsections = _extract_proposal_subsections_from_bid_format(section_content)
                if proposal_subsections:
                    outline["main_sections"] = ["1 方案的详细说明", "2 施工组织设计"]
                    outline["sub_sections"] = {
                        "1 方案的详细说明": proposal_subsections.get("technical", []),
                        "2 施工组织设计": proposal_subsections.get("construction", [])
                    }
                    return outline
    
    # 如果没有找到投标文件格式，尝试直接搜索方案章节
    proposal_patterns = [
        r"方案详细说明及施工组织设计",
        r"方案详细说明",
        r"施工组织设计",
        r"技术方案",
        r"实施方案",
        r"施工方案",
        r"技术实施",
        r"施工组织"
    ]
    
    for pattern in proposal_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start_pos = match.start()
            # 提取该章节内容
            section_content = _extract_section_content(text, start_pos)
            if section_content:
                # 解析章节结构
                sections = _parse_section_structure(section_content)
                outline["main_sections"] = sections.get("main", [])
                outline["sub_sections"] = sections.get("sub", {})
                return outline
    
    # 如果仍然没有找到特定章节，使用通用结构
    outline = _generate_generic_outline(text)
    
    return outline


def _find_proposal_section_in_outline(outline_sections: List[str]) -> Optional[str]:
    """从招标文件骨架章节列表中查找方案相关章节"""
    proposal_keywords = [
        "方案详细说明及施工组织设计",
        "方案详细说明", 
        "施工组织设计",
        "技术方案",
        "实施方案",
        "施工方案",
        "方案"
    ]
    
    for section in outline_sections:
        # 清理章节名称（去除编号和特殊字符）
        clean_section = re.sub(r'^\d+[\.、]?\s*', '', section)
        clean_section = re.sub(r'[（）()\[\]【】]', '', clean_section)
        
        # 检查是否包含方案关键词
        for keyword in proposal_keywords:
            if keyword in clean_section:
                return section
    
    return None


def _extract_specific_section_content(text: str, section_title: str) -> Optional[str]:
    """根据具体章节标题提取内容"""
    # 清理标题以进行匹配
    clean_title = re.sub(r'^\d+[\.、]?\s*', '', section_title)
    clean_title = re.escape(clean_title.strip())
    
    # 查找章节开始位置
    pattern = rf"{clean_title}[\s\S]*?\n(?=#|\d+[\.、]\s*[^\s]|$)"
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        return match.group(0).strip()
    
    return None


def _extract_bid_format_section_content(text: str, start_pos: int) -> Optional[str]:
    """提取投标文件格式章节内容"""
    # 查找章节结束位置（通常是下一个主要章节开始）
    end_patterns = [
        r"第六章", r"第6章", r"6\.",
        r"第七章", r"第7章", r"7\.",
        r"第八章", r"第8章", r"8\.",
        r"第九章", r"第9章", r"9\.",
        r"评标", r"评分", r"评审"
    ]
    
    # 从开始位置向后搜索结束标记
    remaining_text = text[start_pos:]
    end_match = None
    
    for pattern in end_patterns:
        end_match = re.search(pattern, remaining_text, re.IGNORECASE)
        if end_match:
            break
    
    if end_match:
        return remaining_text[:end_match.start()].strip()
    else:
        # 如果没有找到结束标记，取一定长度的文本
        return remaining_text[:8000].strip() if len(remaining_text) > 8000 else remaining_text.strip()


def _extract_section_content(text: str, start_pos: int) -> Optional[str]:
    """提取指定位置开始的章节内容"""
    # 查找章节结束位置（通常是下一个主要章节开始）
    end_patterns = [
        r"第九章", r"第9章", r"9\.",
        r"第十章", r"第10章", r"10\.",
        r"商务和技术偏差表",
        r"资格审查资料",
        r"其他资料"
    ]
    
    # 从开始位置向后搜索结束标记
    remaining_text = text[start_pos:]
    end_match = None
    
    for pattern in end_patterns:
        end_match = re.search(pattern, remaining_text, re.IGNORECASE)
        if end_match:
            break
    
    if end_match:
        return remaining_text[:end_match.start()].strip()
    else:
        # 如果没有找到结束标记，取一定长度的文本
        return remaining_text[:5000].strip() if len(remaining_text) > 5000 else remaining_text.strip()


def _extract_proposal_subsections_from_bid_format(content: str) -> Dict[str, List[str]]:
    """从投标文件格式内容中提取方案相关的子章节"""
    result = {"technical": [], "construction": []}
    
    # 常见方案相关的关键词
    technical_keywords = [
        "方案", "技术", "设计", "优化", "改造", "工艺", "系统", 
        "设备", "配置", "路由", "管网", "捕集", "尘源", "关键",
        "详细说明", "说明", "图纸", "布置图"
    ]
    
    construction_keywords = [
        "施工", "组织", "方法", "措施", "工序", "流程", "质量", 
        "安全", "进度", "资源", "配合", "停机", "时间", "文明",
        "环保", "验收", "试车"
    ]
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 检查是否是编号条目
        numbered_match = re.match(r'^(\d+(?:\.\d+)*)[、.)]\s*(.+)$', line)
        if numbered_match:
            number = numbered_match.group(1)
            title = numbered_match.group(2).strip()
            
            # 判断是技术方案还是施工组织
            is_technical = any(keyword in title for keyword in technical_keywords)
            is_construction = any(keyword in title for keyword in construction_keywords)
            
            if is_technical and not is_construction:
                result["technical"].append(f"{number} {title}")
            elif is_construction:
                result["construction"].append(f"{number} {title}")
            elif '.' in number:  # 子条目，根据父条目判断
                main_num = number.split('.')[0]
                # 检查父条目类型
                parent_is_technical = any(main_num in item for item in result["technical"])
                parent_is_construction = any(main_num in item for item in result["construction"])
                
                if parent_is_technical:
                    result["technical"].append(f"{number} {title}")
                elif parent_is_construction:
                    result["construction"].append(f"{number} {title}")
        
        # 检查列表项
        elif re.match(r'^[-*•]\s+(.+)$', line):
            item = re.sub(r'^[-*•]\s+', '', line).strip()
            
            is_technical = any(keyword in item for keyword in technical_keywords)
            is_construction = any(keyword in item for keyword in construction_keywords)
            
            if is_technical and not is_construction:
                result["technical"].append(f"• {item}")
            elif is_construction:
                result["construction"].append(f"• {item}")
    
    return result


def _parse_section_structure(content: str) -> Dict[str, List[str]]:
    """解析章节结构，提取主要章节和子章节"""
    result = {"main": [], "sub": {}}
    
    # 匹配多种编号格式：1. 1、 1) (1) ①等
    numbered_patterns = [
        r"^(\d+(?:\.\d+)*)\s*[、.:]?\s*([^\n]+)$",  # 1.1, 1.2
        r"^(\d+)\s*[、]\s*([^\n]+)$",  # 1、标题
        r"^(\d+)\s*[.)]\s*([^\n]+)$",  # 1.标题 或 1)标题
        r"^[(（]\s*(\d+)\s*[)）]\s*([^\n]+)$",  # (1)标题
    ]
    
    lines = content.split('\n')
    current_main = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 检查是否是编号章节
        matched = False
        for pattern in numbered_patterns:
            match = re.match(pattern, line)
            if match:
                number = match.group(1)
                title = match.group(2).strip()
                
                # 判断是主章节还是子章节
                if '.' in number or (len(number) > 1 and number.isdigit()):
                    # 子章节（如 1.1, 1.2, 2.1）或多位数字（如11、12）
                    main_num = number.split('.')[0] if '.' in number else number[0]
                    if current_main and main_num == current_main.split(' ')[0]:
                        if current_main not in result["sub"]:
                            result["sub"][current_main] = []
                        result["sub"][current_main].append(f"{number} {title}")
                else:
                    # 主章节
                    result["main"].append(f"{number} {title}")
                    current_main = f"{number} {title}"
                
                matched = True
                break
        
        if not matched and line.startswith(('*', '-', '•', '○', '●')) and current_main:
            # 列表项，作为子章节
            if current_main not in result["sub"]:
                result["sub"][current_main] = []
            result["sub"][current_main].append(line.strip('* -•○●').strip())
    
    return result


def _generate_generic_outline(text: str) -> Dict[str, List[str]]:
    """生成通用方案提纲"""
    return {
        "main_sections": [
            "1 项目概述与背景",
            "2 技术方案设计",
            "3 施工组织设计", 
            "4 质量管理体系",
            "5 安全管理措施",
            "6 进度计划安排",
            "7 资源配置计划",
            "8 环境保护措施",
            "9 应急预案",
            "10 成果交付与验收"
        ],
        "sub_sections": {
            "1 项目概述与背景": [
                "1.1 项目基本情况",
                "1.2 建设背景与必要性",
                "1.3 项目目标与范围",
                "1.4 相关规范标准"
            ],
            "2 技术方案设计": [
                "2.1 总体技术方案",
                "2.2 关键技术说明", 
                "2.3 设备选型与配置",
                "2.4 系统集成方案",
                "2.5 技术创新点"
            ],
            "3 施工组织设计": [
                "3.1 施工总体部署",
                "3.2 施工方法及技术措施",
                "3.3 施工工艺流程",
                "3.4 质量控制措施",
                "3.5 安全文明施工"
            ]
        }
    }


def generate_proposal_markdown(outline: Dict[str, List[str]], title: str = "技术方案提案") -> str:
    """根据提纲生成Markdown格式的提案"""
    md_content = f"# {title}\n\n"
    
    # 添加主要章节
    for section in outline["main_sections"]:
        md_content += f"## {section}\n\n"
        
        # 添加对应的子章节
        if section in outline["sub_sections"]:
            for sub_section in outline["sub_sections"][section]:
                md_content += f"### {sub_section}\n\n"
                md_content += "*此处填写具体内容*\n\n"
        else:
            md_content += "*此处填写具体内容*\n\n"
    
    return md_content


def extract_from_file(file_path: str, outline_sections: List[str] = None) -> Dict[str, List[str]]:
    """从文件提取方案提纲"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return extract_proposal_outline(content, outline_sections)


# 示例用法
if __name__ == "__main__":
    # 示例：从招标文件提取提纲
    try:
        outline = extract_from_file("uploads/招标文件.md")
        proposal_md = generate_proposal_markdown(outline, "钢渣处理项目技术方案")
        print("提取的提纲结构:")
        print(outline)
        print("\n生成的Markdown提案:")
        print(proposal_md)
    except FileNotFoundError:
        print("招标文件不存在，使用通用模板")
        outline = _generate_generic_outline("")
        proposal_md = generate_proposal_markdown(outline, "技术方案提案")
        print(proposal_md)