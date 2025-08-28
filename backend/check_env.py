#!/usr/bin/env python3
"""
环境变量检查脚本
检查后端所需的环境变量是否正确配置
"""

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app_core.config import settings
except ImportError as e:
    print(f"❌ 导入配置失败: {e}")
    print("请确保在backend目录下运行此脚本")
    sys.exit(1)

def check_env():
    print("🔍 环境变量检查")
    print("=" * 50)
    
    # 检查基本配置
    print(f"📍 环境类型: {settings.ENVIRONMENT}")
    print(f"🐛 调试模式: {'启用' if settings.DEBUG else '禁用'}")
    print(f"🌐 服务器地址: {settings.HOST}:{settings.PORT}")
    print(f"📁 上传目录: {settings.UPLOAD_DIR}")
    print(f"📏 最大文件大小: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB")
    
    print("\n🔑 API密钥检查")
    print("-" * 30)
    
    # 检查API密钥
    api_keys = {
        "OpenRouter": settings.OPENROUTER_API_KEY,
        "OpenAI": settings.OPENAI_API_KEY,
        "Anthropic": settings.ANTHROPIC_API_KEY
    }
    
    configured_keys = []
    for name, key in api_keys.items():
        status = "✅ 已配置" if key and key.strip() else "❌ 未配置"
        print(f"{name:12}: {status}")
        if key and key.strip():
            configured_keys.append(name)
    
    if not configured_keys:
        print("\n⚠️  警告: 没有配置任何LLM API密钥！")
        print("请至少配置一个API密钥才能使用系统。")
        return False
    else:
        print(f"\n✅ 已配置 {len(configured_keys)} 个API密钥: {', '.join(configured_keys)}")
    
    print("\n🔐 安全配置检查")
    print("-" * 30)
    
    # 检查安全配置
    secret_key_ok = settings.SECRET_KEY != "your-secret-key-change-this"
    jwt_key_ok = settings.JWT_SECRET_KEY != "your-jwt-secret-key-change-this"
    
    print(f"Secret Key: {'✅ 已修改' if secret_key_ok else '❌ 使用默认值'}")
    print(f"JWT Secret: {'✅ 已修改' if jwt_key_ok else '❌ 使用默认值'}")
    
    if not secret_key_ok or not jwt_key_ok:
        print("⚠️  警告: 生产环境请修改默认的安全密钥！")
    
    print("\n🌐 CORS配置")
    print("-" * 30)
    print(f"允许的域名: {', '.join(settings.BACKEND_CORS_ORIGINS)}")
    
    print("\n📊 总结")
    print("=" * 50)
    
    if not configured_keys:
        print("❌ 配置不完整 - 缺少LLM API密钥")
        return False
    elif settings.ENVIRONMENT == "production" and (not secret_key_ok or not jwt_key_ok):
        print("⚠️  生产环境配置有安全风险 - 请修改默认密钥")
        return True
    else:
        print("✅ 环境配置检查通过")
        return True

def check_directories():
    """检查必要的目录"""
    print("\n📂 目录检查")
    print("-" * 30)
    
    directories = [
        settings.UPLOAD_DIR,
        "./sessions",
        "./wiki"
    ]
    
    for dir_path in directories:
        if os.path.exists(dir_path):
            print(f"{dir_path:15}: ✅ 存在")
        else:
            print(f"{dir_path:15}: ❌ 不存在，将自动创建")
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"{dir_path:15}: ✅ 已创建")
            except Exception as e:
                print(f"{dir_path:15}: ❌ 创建失败 - {e}")

def check_dependencies():
    """检查关键依赖"""
    print("\n📦 依赖检查")
    print("-" * 30)
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "pydantic_settings",
        "langgraph",
        "langchain",
        "openai",
        "anthropic",
        "pypdf2",
        "python-docx",
        "aiofiles"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"{package:20}: ✅ 已安装")
        except ImportError:
            print(f"{package:20}: ❌ 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Solution Agent 环境检查")
    print("=" * 50)
    
    env_ok = check_env()
    check_directories()
    deps_ok = check_dependencies()
    
    print("\n" + "=" * 50)
    if env_ok and deps_ok:
        print("🎉 所有检查通过！可以启动服务器。")
        print("\n启动命令:")
        print("python dev.py")
    else:
        print("❌ 存在配置问题，请修复后重试。")
        sys.exit(1)