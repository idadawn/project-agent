#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工作流集成
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from workflow.bid_build_graph import build_bid_graph
from workflow.state import BidState

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

def test_workflow_integration():
    """测试工作流集成"""
    print("🧪 测试工作流集成...")
    
    # 构建工作流
    graph = build_bid_graph()
    print("✅ 工作流构建成功")
    
    # 创建测试状态
    initial_state = BidState({
        "session_id": "test_session",
        "uploaded_files": [],
        "parsed_documents": [{
            'filename': 'test.md',
            'content': test_document
        }],
        "project_state": {},
        "wiki_dir": "test_wiki"
    })
    
    # 只运行到 outline_extractor 节点
    print("🚀 运行到 outline_extractor 节点...")
    
    # 执行 structure_extractor -> outline_extractor
    state_after_structure = graph.nodes["structure_extractor"].invoke(initial_state)
    print("✅ structure_extractor 执行完成")
    
    state_after_outline = graph.nodes["outline_extractor"].invoke(state_after_structure)
    print("✅ outline_extractor 执行完成")
    
    # 检查结果
    if "outline_results" in state_after_outline:
        results = state_after_outline["outline_results"]
        matched_ok = sum(1 for r in results if r['status'] == "ok")
        matched_low = sum(1 for r in results if r['status'] == "low_confidence")
        matched_missing = sum(1 for r in results if r['status'] == "missing")
        
        print(f"📊 抽取结果: {matched_ok}个精确匹配, {matched_low}个低置信度, {matched_missing}个缺失")
        print(f"🔧 状态: {state_after_outline.get('outline_extraction_status', 'unknown')}")
        
        if matched_ok > 0:
            print("✅ 工作流集成测试成功!")
            return True
        else:
            print("⚠️  工作流集成测试完成，但未找到匹配章节")
            return False
    else:
        print("❌ outline_extractor 未返回结果")
        return False

if __name__ == "__main__":
    success = test_workflow_integration()
    if success:
        print("\n🎉 所有测试通过!")
    else:
        print("\n❌ 测试失败")
        sys.exit(1)