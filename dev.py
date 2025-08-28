#!/usr/bin/env python3
"""
开发服务器启动脚本
运行命令: python dev.py
"""
import sys
import os

# 将项目根目录添加到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 将 backend 目录添加到 Python 路径
backend_dir = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动开发服务器...")
    print("📍 API 地址: http://localhost:8001")
    print("📚 API 文档: http://localhost:8001/docs")
    print("⚡ 按 Ctrl+C 停止服务器")
    
    # 使用模块字符串而不是导入的app对象来支持reload
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, log_level="info", reload=True)