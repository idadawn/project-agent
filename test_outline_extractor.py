#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试方案提纲抽取智能体
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from agents.outline_extractor import OutlineExtractorAgent
from agents.base import AgentContext

# 创建测试文档
test_document = """
# 招标文件

## 第一章 项目概况
本项目是某钢铁公司钢渣处理系统优化改造项目。

## 第二章 技术要求
要求投标人具备相关资质和经验。

## 第三章 投标文件格式

### 一、投标函
### 二、法定代表人身份证明  
### 三、授权委托书
### 四、投标保证金
### 五、投标报价表
### 六、分项报价表
### 七、企业资料
### 八、方案详细说明及施工组织设计

#### 1、方案的详细说明

##### 1.1 优化提升改造部分详细方案说明
本项目主要对现有钢渣处理系统进行优化改造。

##### 1.2 尘源点捕集罩方案详细说明
采用高效吸风罩对尘源点进行捕集。

##### 1.3 平面管网路由方案图及说明
管网布置沿现有工艺路线进行优化。

##### 1.4 钢渣一次处理工艺系统方案图及详细说明
一次处理系统采用先进工艺技术。

##### 1.5 除尘系统布置图及方案详细说明
除尘系统合理布局，确保排放达标。

##### 1.6 关键技术说明等
包括系统集成、自动化控制等关键技术。

#### 2、施工组织设计

##### 2.1 施工方法及主要技术措施
采用分段施工，确保工程质量。

##### 2.2 需投标人配合停机时间的详细组织设计
详细规划停机时间，最小化生产影响。

### 九、资格审查资料
### 十、商务和技术偏差表
### 十一、其他材料
"""

def test_outline_extractor():
    """测试提纲抽取功能"""
    print("🧪 测试方案提纲抽取智能体...")
    
    # 创建智能体实例
    agent = OutlineExtractorAgent()
    
    # 创建测试上下文
    context = AgentContext(
        user_input="抽取方案结构",
        uploaded_files=[],
        file_summaries=[],
        selected_text="",
        surrounding_context="",
        existing_content="",
        parsed_documents=[{
            'filename': 'test.md',
            'content': test_document
        }],
        extracted_info={},
        project_state={},
        task_type="bid_processing"
    )
    
    # 执行抽取 - 使用新的字典状态接口
    state = {
        "user_input": "抽取方案结构",
        "uploaded_files": [],
        "parsed_documents": [{
            'filename': 'test.md',
            'content': test_document
        }],
        "project_state": {}
    }
    
    result_state = agent.execute(state)
    
    print("\n📋 抽取结果:")
    if "outline_results" in result_state:
        results = result_state["outline_results"]
        matched_ok = sum(1 for r in results if r['status'] == "ok")
        matched_low = sum(1 for r in results if r['status'] == "low_confidence")
        matched_missing = sum(1 for r in results if r['status'] == "missing")
        total = len(results)
        
        print(f"✅ 方案结构抽取完成 ({matched_ok}个精确匹配, {matched_low}个低置信度, {matched_missing}个缺失)\n")
        
        for i, result in enumerate(results, 1):
            if result['status'] == "ok":
                status_icon = "✅"
                status_text = "精确匹配"
            elif result['status'] == "low_confidence":
                status_icon = "⚠️"
                status_text = "低置信度"
            else:
                status_icon = "❌"
                status_text = "缺失"
            
            print(f"{status_icon} {result['normalized_key']} ({status_text})")
            if result['found_title']:
                print(f"   → {result['found_title']} (置信度: {result['confidence']:.2f})")
            if result.get('content_preview'):
                print(f"   📝 内容预览: {result['content_preview']}")
            print()
    
    print("\n📊 状态信息:")
    for key, value in result_state.items():
        if key == "outline_results":
            print(f"  {key}: [列表长度: {len(value)}]")
        elif key not in ["user_input", "uploaded_files", "parsed_documents", "project_state"]:
            print(f"  {key}: {value}")
    
    print("✅ 测试完成!")

if __name__ == "__main__":
    test_outline_extractor()