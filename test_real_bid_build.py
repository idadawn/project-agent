#!/usr/bin/env python3
"""
使用真实招标文件测试投标文件构建工作流
"""

import os
import sys
import pathlib

# 添加backend目录到Python路径
backend_dir = pathlib.Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from workflow.bid_build_graph import run_build

def test_with_real_tender():
    """使用真实招标文件测试"""
    print("🚀 开始使用真实招标文件测试...")
    
    # 检查是否存在真实的招标文件
    real_tender_path = "wiki/招标文件.md"
    if not os.path.exists(real_tender_path):
        print(f"❌ 未找到真实招标文件: {real_tender_path}")
        print("请确保 wiki/招标文件.md 文件存在")
        return
    
    print(f"📄 使用真实招标文件: {real_tender_path}")
    
    # 创建wiki目录
    wiki_dir = pathlib.Path("wiki")
    wiki_dir.mkdir(exist_ok=True)
    
    try:
        # 运行工作流
        print("🔄 运行A-E工作流...")
        result = run_build(
            session_id="real_test_session",
            tender_path=real_tender_path,
            wiki_dir="wiki",
            meta={
                "project_name": "真实项目测试",
                "tender_no": "REAL-2024-001",
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
            print("\n📄 投标文件骨架 (前500字符):")
            with open(result['outline_path'], 'r', encoding='utf-8') as f:
                content = f.read()
                print(content[:500] + "..." if len(content) > 500 else content)
        
        if result.get('spec_path') and os.path.exists(result['spec_path']):
            print("\n📄 技术规格书提取 (前500字符):")
            with open(result['spec_path'], 'r', encoding='utf-8') as f:
                content = f.read()
                print(content[:500] + "..." if len(content) > 500 else content)
        
        if result.get('plan_path') and os.path.exists(result['plan_path']):
            print("\n📄 方案提纲 (前500字符):")
            with open(result['plan_path'], 'r', encoding='utf-8') as f:
                content = f.read()
                print(content[:500] + "..." if len(content) > 500 else content)
        
        if result.get('draft_path') and os.path.exists(result['draft_path']):
            print("\n📄 投标文件草案 (前500字符):")
            with open(result['draft_path'], 'r', encoding='utf-8') as f:
                content = f.read()
                print(content[:500] + "..." if len(content) > 500 else content)
        
        if result.get('sanity_report'):
            print("\n📊 校验报告:")
            import json
            print(json.dumps(result['sanity_report'], ensure_ascii=False, indent=2))
        
        print("\n🎉 真实文件测试完成！")
        
    except Exception as e:
        print(f"❌ 工作流执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_with_real_tender()
