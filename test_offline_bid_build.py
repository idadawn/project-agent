#!/usr/bin/env python3
"""
测试A-E工作流构建功能（离线版本）
"""
import asyncio
import os
import sys

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from workflow.bid_build_graph import BidBuildState
from agents.structure_extractor import StructureExtractor
from agents.spec_extractor import SpecExtractor
from agents.bid_assembler import BidAssembler
from agents.sanity_checker import SanityChecker

# Mock plan outliner for offline testing
class MockPlanOutliner:
    async def execute(self, state):
        import pathlib
        import datetime
        
        wiki_dir = "wiki"
        pathlib.Path(wiki_dir).mkdir(parents=True, exist_ok=True)
        
        # Create a mock outline
        outline = """# 方案详细说明及施工组织设计

## A. 技术方案（25分）
- 项目理解与技术路线
- 关键设备与参数  
- 排放与能效保证值
- 系统集成与接口
- 控制与数字化

## B. 施工方法及主要技术措施（25分）
- 组织机构与职责
- 关键工序与质量控制
- 干扰最小化与应急回退
- 安全文明与环保
- 试车与验收

## C. 进度与资源
- 工期里程碑
- 人材机配置

## D. 质量/HSE/风险
- 质量目标与流程
- 风险矩阵与缓解

## E. 资料与培训
- 资料清单与份数
- 培训与考核
"""
        
        head = f"""---
title: 方案（提纲）
generated_at: {datetime.date.today().strftime("%Y-%m-%d")}
---

"""
        
        out = os.path.join(wiki_dir, "方案_提纲.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(head + outline + "\n")
        
        state["plan_path"] = out
        state["current_content"] = "成功生成方案提纲（离线模拟）"
        state["current_stage"] = "plan_outlining_completed"
        
        return state

async def test_offline_bid_build():
    """测试离线投标文件构建工作流"""
    print("🚀 开始测试A-E工作流（离线版本）...")
    
    # 模拟上传文件
    test_content = """
# 第四章 技术规格书

## 4.1 项目概述
本项目要求建设一个智能化系统，包括硬件设备和软件平台。

## 4.2 技术要求
- 系统响应时间：≤2秒
- 可用性：≥99.9%
- 数据安全性：符合等保三级要求

## 4.3 交付要求
- 项目工期：90天
- 验收标准：通过第三方检测
- 资料交付：全套技术文档

# 第五章 投标文件格式

投标文件应包括以下内容：
1. 投标函
2. 法定代表人身份证明  
3. 授权委托书
4. 投标保证金
5. 投标报价表
6. 分项报价表
7. 企业资料
8. 方案详细说明及施工组织设计
9. 资格审查资料
10. 商务和技术偏差表
11. 其他材料
"""
    
    # 创建初始状态
    state = BidBuildState({
        "session_id": "test_session_offline",
        "uploaded_files": [{
            "filename": "招标文件.md",
            "file_type": "text/markdown",
            "content": test_content
        }],
        "wiki_dir": "wiki_test",
        "meta": {"project_name": "测试项目"},
        "project_state": {}
    })
    
    try:
        # 创建agent实例
        structure_extractor = StructureExtractor()
        spec_extractor = SpecExtractor()
        plan_outliner = MockPlanOutliner()  # 使用模拟版本
        bid_assembler = BidAssembler()
        sanity_checker = SanityChecker()
        
        # 依次执行A-E节点
        print("📝 执行A节点：StructureExtractor...")
        state = await structure_extractor.execute(state)
        print(f"   结果：{state.get('current_content', 'N/A')}")
        
        print("🔧 执行B节点：SpecExtractor...")
        state = await spec_extractor.execute(state)
        print(f"   结果：{state.get('current_content', 'N/A')}")
        
        print("📋 执行C节点：PlanOutliner...")
        state = await plan_outliner.execute(state)
        print(f"   结果：{state.get('current_content', 'N/A')}")
        
        print("🔨 执行D节点：BidAssembler...")
        state = await bid_assembler.execute(state)
        print(f"   结果：{state.get('current_content', 'N/A')}")
        
        print("✅ 执行E节点：SanityChecker...")
        state = await sanity_checker.execute(state)
        print(f"   结果：{state.get('current_content', 'N/A')}")
        
        print("✅ 工作流执行成功！")
        print(f"📄 草案路径: {state.get('draft_path')}")
        print(f"📋 骨架路径: {state.get('outline_path')}")
        print(f"🔧 规格书路径: {state.get('spec_path')}")
        print(f"📝 方案路径: {state.get('plan_path')}")
        print(f"✅ 检查报告: {state.get('sanity_report_path')}")
        
        # 检查生成的文件
        for file_key in ['draft_path', 'outline_path', 'spec_path', 'plan_path', 'sanity_report_path']:
            file_path = state.get(file_key)
            if file_path and os.path.exists(file_path):
                print(f"📁 {file_key}: 文件存在 ({os.path.getsize(file_path)} bytes)")
            else:
                print(f"❌ {file_key}: 文件不存在")
        
        return True
        
    except Exception as e:
        print(f"❌ 工作流执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_offline_bid_build())
    if success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n💥 测试失败！")
        sys.exit(1)