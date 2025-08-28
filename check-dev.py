#!/usr/bin/env python3
"""
开发环境检查脚本
诊断自动重载问题并提供解决方案
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_environment():
    """检查Python环境"""
    print("🐍 Python Environment Check:")
    print(f"   Python Version: {sys.version}")
    print(f"   Python Path: {sys.executable}")
    
    # 检查虚拟环境
    backend_venv = Path("backend/.venv")
    if backend_venv.exists():
        print("   ✅ Backend virtual environment exists")
    else:
        print("   ❌ Backend virtual environment missing")
        print("      Run: cd backend && uv venv --python 3.11 && uv sync")
    
    print()

def check_node_environment():
    """检查Node.js环境"""
    print("📦 Node.js Environment Check:")
    try:
        node_version = subprocess.check_output(["node", "--version"], text=True).strip()
        npm_version = subprocess.check_output(["npm", "--version"], text=True).strip()
        print(f"   Node Version: {node_version}")
        print(f"   NPM Version: {npm_version}")
        
        # 检查node_modules
        frontend_modules = Path("frontend/node_modules")
        if frontend_modules.exists():
            print("   ✅ Frontend dependencies installed")
        else:
            print("   ❌ Frontend dependencies missing")
            print("      Run: cd frontend && npm install")
            
    except subprocess.CalledProcessError:
        print("   ❌ Node.js not found")
        print("      Install Node.js from https://nodejs.org/")
    
    print()

def check_file_watchers():
    """检查文件监控系统"""
    print("👀 File Watcher Check:")
    
    if platform.system() == "Linux":
        try:
            # 检查inotify限制
            result = subprocess.check_output(["cat", "/proc/sys/fs/inotify/max_user_watches"], text=True)
            max_watches = int(result.strip())
            print(f"   Max file watches: {max_watches}")
            
            if max_watches < 524288:
                print("   ⚠️  File watch limit might be too low")
                print("      Increase with: echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf")
            else:
                print("   ✅ File watch limit is adequate")
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("   ❓ Unable to check inotify limits")
    
    elif platform.system() == "Darwin":
        print("   ℹ️  macOS: Using FSEvents (should work automatically)")
    
    elif platform.system() == "Windows":
        print("   ℹ️  Windows: Using native file watching")
    
    print()

def check_port_availability():
    """检查端口可用性"""
    print("🔌 Port Availability Check:")
    
    import socket
    
    ports_to_check = [3000, 8001]
    
    for port in ports_to_check:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"   ⚠️  Port {port} is already in use")
            if port == 3000:
                print("      Frontend port occupied - kill existing Next.js server")
            elif port == 8001:
                print("      Backend port occupied - kill existing uvicorn server")
        else:
            print(f"   ✅ Port {port} is available")
    
    print()

def provide_recommendations():
    """提供优化建议"""
    print("💡 Development Optimization Recommendations:")
    print("   1. Use the enhanced dev scripts:")
    print("      • Backend: python backend/dev.py")
    print("      • Frontend: npm run dev (in frontend directory)")
    print("   2. Or use the one-click starter: ./start-dev.sh")
    print("   3. If auto-reload still doesn't work:")
    print("      • Check file permissions")
    print("      • Try polling mode (already configured)")
    print("      • Disable antivirus real-time scanning on project folder")
    print("   4. For fastest development:")
    print("      • Use SSD storage")
    print("      • Close unnecessary applications")
    print("      • Use terminal instead of IDE integrated terminal")
    print()

def main():
    print("🔧 Solution Agent Development Environment Checker")
    print("=" * 50)
    print()
    
    # 检查是否在项目根目录
    if not Path("CLAUDE.md").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    check_python_environment()
    check_node_environment()
    check_file_watchers()
    check_port_availability()
    provide_recommendations()
    
    print("🎉 Environment check complete!")
    print("If you're still experiencing issues, try restarting the development servers.")

if __name__ == "__main__":
    main()