#!/usr/bin/env python3
"""
测试A-E工作流构建功能
"""
import asyncio
import os
import sys

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from workflow.bid_build_graph import run_build

async def test_bid_build():
    """测试投标文件构建工作流"""
    print("🚀 开始测试A-E工作流...")
    
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
    
    uploaded_files = [
        {
            "filename": "招标文件.md",
            "file_type": "text/markdown",
            "content": test_content
        }
    ]
    
    try:
        result = await run_build(
            session_id="test_session",
            uploaded_files=uploaded_files,
            wiki_dir="wiki_test",
            meta={"project_name": "测试项目"}
        )
        
        print("✅ 工作流执行成功！")
        print(f"📄 草案路径: {result.get('draft_path')}")
        print(f"📋 骨架路径: {result.get('outline_path')}")
        print(f"🔧 规格书路径: {result.get('spec_path')}")
        print(f"📝 方案路径: {result.get('plan_path')}")
        print(f"✅ 检查报告: {result.get('sanity_report_path')}")
        
        # 检查生成的文件
        for file_key in ['draft_path', 'outline_path', 'spec_path', 'plan_path', 'sanity_report_path']:
            file_path = result.get(file_key)
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
    success = asyncio.run(test_bid_build())
    if success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n💥 测试失败！")
        sys.exit(1)