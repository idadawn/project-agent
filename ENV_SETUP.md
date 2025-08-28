# 环境变量配置指南

## 🚀 快速开始

### 1. 后端环境变量设置

```bash
cd backend
cp .env.example .env
```

然后编辑 `.env` 文件，至少需要配置以下必要项：

```bash
# 必须配置的LLM API密钥（选择其一或多个）
OPENROUTER_API_KEY=sk-or-v1-your-key-here  # 推荐使用
# 或
OPENAI_API_KEY=sk-your-openai-key-here
# 或  
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# 安全密钥（生产环境必须修改）
SECRET_KEY=your-unique-secret-key-here
```

### 2. 前端环境变量设置

```bash
cd frontend
cp .env.example .env.local
```

通常前端的默认配置即可使用，如需修改后端地址：

```bash
# 如果后端部署在其他地址
NEXT_PUBLIC_API_BASE_URL=http://your-backend-url:8001
```

## 📋 详细配置说明

### 后端环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|-------|------|--------|------|
| `OPENROUTER_API_KEY` | ✅ | - | OpenRouter API密钥，支持多种模型 |
| `OPENAI_API_KEY` | 可选 | - | OpenAI API密钥 |
| `ANTHROPIC_API_KEY` | 可选 | - | Anthropic Claude API密钥 |
| `SECRET_KEY` | ✅ | - | 应用安全密钥，生产环境必须修改 |
| `PORT` | 否 | 8001 | 后端服务端口 |
| `BACKEND_CORS_ORIGINS` | 否 | localhost:3000 | 允许的前端域名 |
| `MAX_FILE_SIZE` | 否 | 50MB | 最大文件上传大小 |

### 前端环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|-------|------|--------|------|
| `NEXT_PUBLIC_API_BASE_URL` | ✅ | localhost:8001 | 后端API地址 |
| `NEXT_PUBLIC_ENABLE_FILE_UPLOAD` | 否 | true | 是否启用文件上传 |
| `NEXT_PUBLIC_MAX_FILE_SIZE` | 否 | 50MB | 前端文件大小限制 |
| `NEXT_PUBLIC_DEBUG` | 否 | false | 是否启用调试模式 |

## 🔑 获取API密钥

### OpenRouter (推荐)
1. 访问 [OpenRouter](https://openrouter.ai/keys)
2. 注册账号并获取API密钥
3. 支持多种模型，价格透明

### OpenAI
1. 访问 [OpenAI Platform](https://platform.openai.com/api-keys)
2. 登录并创建API密钥
3. 需要绑定付费方式

### Anthropic
1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册并获取API密钥
3. 支持Claude系列模型

## 🌍 部署环境配置

### 开发环境
```bash
# 后端
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# 前端  
NEXT_PUBLIC_DEBUG=true
```

### 生产环境
```bash
# 后端
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your-strong-production-secret-key

# 前端
NEXT_PUBLIC_DEBUG=false
NEXT_PUBLIC_API_BASE_URL=https://your-production-api.com
```

## 🔒 安全注意事项

1. **永远不要提交包含真实密钥的 `.env` 文件到版本控制**
2. **生产环境必须修改 `SECRET_KEY`**
3. **定期轮换API密钥**
4. **使用强随机字符串作为密钥**

## 🛠️ 故障排除

### 常见问题

**后端启动失败：**
```bash
# 检查环境变量是否正确加载
cd backend
python -c "from app_core.config import settings; print(settings.OPENROUTER_API_KEY)"
```

**前端API调用失败：**
```bash
# 检查后端地址是否正确
curl http://localhost:8001/api/v1/
```

**文件上传失败：**
- 检查 `MAX_FILE_SIZE` 设置
- 确保 `uploads/` 目录有写权限
- 验证文件格式是否支持

### 环境变量验证

创建验证脚本：

```bash
# backend/check_env.py
from app_core.config import settings

print("✅ Environment Variables Check:")
print(f"API Keys configured: {bool(settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY)}")
print(f"Secret Key: {'✅ Set' if settings.SECRET_KEY != 'your-secret-key-change-this' else '❌ Default'}")
print(f"Port: {settings.PORT if hasattr(settings, 'PORT') else '8001'}")
```

## 📞 获取帮助

如果遇到配置问题：
1. 检查 `.env` 文件格式是否正确
2. 确认API密钥有效性
3. 查看服务器日志获取详细错误信息
4. 参考项目 README.md 获取更多信息