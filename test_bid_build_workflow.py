#!/usr/bin/env python3
"""
测试投标文件构建工作流
"""

import os
import sys
import pathlib

# 添加backend目录到Python路径
backend_dir = pathlib.Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from workflow.bid_build_graph import run_build
from workflow.state import BidState

def test_bid_workflow():
    """测试A-E工作流"""
    print("🚀 开始测试投标文件构建工作流...")
    
    # 创建测试用的招标文件
    test_tender_content = """# 招标文件

## 第四章 技术规格书

### 4.1 工程概况
本项目为环保设备安装工程，要求达到超低排放标准。

### 4.2 技术要求
- 排放标准：颗粒物≤10mg/m³
- 工期要求：总工期180天，150天具备投产条件
- 质量要求：交钥匙工程

### 4.3 安全环保
- 本质安全设计
- 扬尘控制标准
- 第三方检测要求

## 第五章 投标文件格式

### 5.1 投标文件组成
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

### 5.2 装订要求
- 正本1份，副本4份
- 正副本分别装订成册并编目录
- 不得用可拆换装订

## 第六章 评标办法

### 6.1 评分标准
- 施工组织设计方案：50分
  - 技术方案：25分
  - 施工方法及主要技术措施：25分
- 报价：45分
- 业绩：3分
- 工期：2分
"""
    
    # 创建uploads目录和测试文件
    uploads_dir = pathlib.Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    test_tender_path = uploads_dir / "招标文件.md"
    with open(test_tender_path, "w", encoding="utf-8") as f:
        f.write(test_tender_content)
    
    print(f"📄 创建测试招标文件: {test_tender_path}")
    
    # 创建wiki目录
    wiki_dir = pathlib.Path("wiki")
    wiki_dir.mkdir(exist_ok=True)
    
    try:
        # 运行工作流
        print("🔄 运行A-E工作流...")
        result = run_build(
            session_id="test_session",
            tender_path=str(test_tender_path),
            wiki_dir="wiki",
            meta={
                "project_name": "环保设备安装工程",
                "tender_no": "TEST-2024-001",
                "bidder_name": "测试投标人"
            }
        )
        
        print("✅ 工作流执行完成！")
        print(f"📁 输出文件:")
        print(f"  - 骨架文件: {result.get('outline_path')}")
        print(f"  - 规格书: {result.get('spec_path')}")
        print(f"  - 方案提纲: {result.get('plan_path')}")
        print(f"  - 投标草案: {result.get('draft_path')}")
        print(f"  - 校验报告: {result.get('sanity_report_path')}")
        
        # 检查生成的文件
        print("\n📋 检查生成的文件内容:")
        
        if result.get('outline_path') and os.path.exists(result['outline_path']):
            print("\n📄 投标文件骨架:")
            with open(result['outline_path'], 'r', encoding='utf-8') as f:
                print(f.read()[:500] + "...")
        
        if result.get('spec_path') and os.path.exists(result['spec_path']):
            print("\n📄 技术规格书提取:")
            with open(result['spec_path'], 'r', encoding='utf-8') as f:
                print(f.read()[:500] + "...")
        
        if result.get('plan_path') and os.path.exists(result['plan_path']):
            print("\n📄 方案提纲:")
            with open(result['plan_path'], 'r', encoding='utf-8') as f:
                print(f.read()[:500] + "...")
        
        if result.get('draft_path') and os.path.exists(result['draft_path']):
            print("\n📄 投标文件草案:")
            with open(result['draft_path'], 'r', encoding='utf-8') as f:
                print(f.read()[:500] + "...")
        
        if result.get('sanity_report'):
            print("\n📊 校验报告:")
            import json
            print(json.dumps(result['sanity_report'], ensure_ascii=False, indent=2))
        
        print("\n🎉 测试完成！")
        
    except Exception as e:
        print(f"❌ 工作流执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        if test_tender_path.exists():
            test_tender_path.unlink()
            print(f"🧹 清理测试文件: {test_tender_path}")

if __name__ == "__main__":
    test_bid_workflow()
