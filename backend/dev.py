#!/usr/bin/env python3
"""
开发服务器启动脚本 - 支持自动重载
"""

import uvicorn
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # 设置环境变量
    os.environ["PYTHONPATH"] = str(project_root)
    
    # 启动开发服务器，with enhanced reload
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8001,
        reload=True,
        reload_dirs=[str(project_root)],  # 明确指定重载目录
        reload_excludes=["__pycache__", "*.pyc", ".venv", "sessions"],  # 排除不需要监控的目录
        log_level="info",
        access_log=True,
        reload_delay=0.25,  # 减少重载延迟
    )