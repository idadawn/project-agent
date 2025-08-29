#!/usr/bin/env python3
"""
检查.env配置文件是否被正确读取
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_core.config import settings

def check_env_loading():
    print("🔍 检查.env配置文件读取状态")
    print("=" * 50)
    
    # 检查.env文件是否存在
    env_file_path = os.path.join(os.path.dirname(__file__), ".env")
    print(f"📁 .env文件路径: {env_file_path}")
    print(f"📄 .env文件存在: {'✅' if os.path.exists(env_file_path) else '❌'}")
    
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r', encoding='utf-8') as f:
            lines = len(f.readlines())
        print(f"📊 .env文件行数: {lines}")
    
    print("\n🔧 配置加载检查")
    print("-" * 30)
    
    # 检查关键配置是否被正确读取
    configs_to_check = [
        ("PORT", settings.PORT, "8001"),
        ("HOST", settings.HOST, "0.0.0.0"),
        ("ENVIRONMENT", settings.ENVIRONMENT, "development"),
        ("DEBUG", settings.DEBUG, "true"),
        ("LOG_LEVEL", settings.LOG_LEVEL, "INFO"),
        ("BACKEND_CORS_ORIGINS", settings.BACKEND_CORS_ORIGINS, '["http://localhost:3000","http://localhost:11010"]'),
        ("OPENROUTER_API_KEY", settings.OPENROUTER_API_KEY[:20] + "..." if settings.OPENROUTER_API_KEY else "", "sk-or-v1-..."),
        ("MAX_FILE_SIZE", settings.MAX_FILE_SIZE, "52428800"),
        ("UPLOAD_DIR", settings.UPLOAD_DIR, "./上传文件"),
    ]
    
    for config_name, actual_value, expected_from_env in configs_to_check:
        env_value = os.getenv(config_name, "未设置")
        print(f"\n📋 {config_name}:")
        print(f"   环境变量值: {env_value}")
        print(f"   实际配置值: {actual_value}")
        print(f"   .env文件期望: {expected_from_env}")
        
        # 检查是否从.env读取
        if config_name == "BACKEND_CORS_ORIGINS":
            # 特殊处理CORS配置
            if "http://localhost:11010" in actual_value:
                print(f"   状态: ✅ 已从.env文件读取")
            else:
                print(f"   状态: ❌ 可能未从.env文件读取")
        elif str(actual_value) == str(expected_from_env) or (env_value != "未设置" and str(actual_value) == str(env_value)):
            print(f"   状态: ✅ 已从.env文件读取")
        else:
            print(f"   状态: ⚠️  使用默认值或代码硬编码值")
    
    print("\n🌐 CORS配置详细检查")
    print("-" * 30)
    print(f"实际CORS配置: {settings.BACKEND_CORS_ORIGINS}")
    print(f"是否包含11010端口: {'✅' if 'http://localhost:11010' in settings.BACKEND_CORS_ORIGINS else '❌'}")
    
    print("\n📊 总结")
    print("-" * 30)
    
    # 检查关键API密钥是否配置
    api_keys_configured = []
    if settings.OPENROUTER_API_KEY:
        api_keys_configured.append("OpenRouter")
    if settings.OPENAI_API_KEY:
        api_keys_configured.append("OpenAI")
    if settings.ANTHROPIC_API_KEY:
        api_keys_configured.append("Anthropic")
    
    print(f"✅ 已配置的API密钥: {', '.join(api_keys_configured) if api_keys_configured else '❌ 无'}")
    print(f"✅ 端口配置正确: {'✅' if settings.PORT == 8001 else '❌'}")
    print(f"✅ CORS配置正确: {'✅' if 'http://localhost:11010' in settings.BACKEND_CORS_ORIGINS else '❌'}")
    
    return True

if __name__ == "__main__":
    check_env_loading()