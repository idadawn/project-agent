# Project Agent - 投标文件生成系统

基于 FastAPI + LangGraph + Next.js 的多智能体投标文件处理与生成系统，专注于文档解析、关键信息提取和自动化投标文件生成。

## 系统特性

### 🤖 多智能体架构
- **协调智能体 (Coordinator)**: 总指挥，负责对话管理和任务分派
- **文档解析智能体 (Document Parser)**: 招标文件分析和内容提取
- **关键信息提取智能体 (Key Extraction)**: 技术规格和要求提取
- **投标生成智能体 (Bid Generator)**: 投标文件自动生成
- **格式优化智能体 (Bid Format Agent)**: 文档格式规范化

### 🎯 核心功能
- **智能文档解析**: 支持 PDF、DOCX、TXT、MD 格式的招标文件分析
- **关键信息提取**: 自动识别技术规格、投标要求、格式要求
- **投标文件生成**: 基于解析结果自动生成符合要求的投标文件
- **三面板界面**: 文件树 + Markdown编辑器 + 聊天面板
- **会话管理**: 支持多会话和状态保存

### 🔧 技术栈
- **后端**: FastAPI + LangGraph + Pydantic
- **前端**: Next.js 14 + React + TypeScript + Tailwind CSS
- **LLM支持**: OpenRouter (统一接口，支持多种模型)
- **包管理**: uv (后端) + npm (前端)

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+
- uv 包管理器

### 1. 安装依赖

#### 后端设置
```bash
# 进入后端目录
cd backend

# 创建虚拟环境并安装依赖
uv venv --python 3.11
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows
```

#### 前端设置
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
```

### 2. 环境配置

在项目根目录创建 `.env` 文件：
```bash
# LLM API 密钥 (至少配置一个)
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# 可选其他LLM提供商
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-key

# 应用安全密钥
SECRET_KEY=your-secret-key-here
```

### 3. 启动服务

#### 后端服务
```bash
cd backend
python dev.py  # 启动开发服务器 (localhost:8001)
```

#### 前端服务
```bash
cd frontend  
npm run dev    # 启动开发服务器 (localhost:3000)
```

### 4. 访问应用
- 前端界面: http://localhost:3000
- API文档: http://localhost:8001/docs

## 使用指南

### 基本工作流程

1. **上传招标文件**
   - 在界面中上传招标文件 (PDF、DOCX、TXT、MD格式)
   - 系统自动进行文档解析

2. **信息提取与分析**
   - 系统自动提取技术规格、投标要求等关键信息
   - 分析投标文件格式要求

3. **投标文件生成**
   - 基于提取的信息自动生成投标文件
   - 支持格式规范化和内容优化

4. **编辑与优化**
   - 在Markdown编辑器中查看和编辑生成的内容
   - 支持实时文本优化

### LLM模型配置

系统默认使用 OpenRouter 接口，当前配置：

```python
# backend/app_core/llm_client.py
default_configs = {
    "coordinator": "anthropic/claude-3.5-sonnet",     # 协调智能体
    "document_parser": "anthropic/claude-3-haiku",   # 文档解析 (快速)
    "key_extraction": "anthropic/claude-3.5-sonnet", # 关键信息提取
    "bid_generator": "openai/gpt-4-turbo",           # 投标生成 (创作力强)
}
```

## 项目结构

```
project-agent/
├── backend/                    # FastAPI 后端
│   ├── agents/                # 智能体实现
│   │   ├── base.py           # 基础智能体类
│   │   ├── coordinator.py    # 协调智能体
│   │   ├── document_parser.py # 文档解析智能体
│   │   ├── key_extraction.py # 信息提取智能体
│   │   ├── bid_generator.py  # 投标生成智能体
│   │   └── bid_format_agent.py # 格式优化智能体
│   ├── api/v1/endpoints/     # API 路由
│   │   ├── chat.py          # 聊天接口
│   │   ├── files.py         # 文件上传
│   │   ├── sessions.py      # 会话管理
│   │   └── proposals.py     # 投标管理
│   ├── app_core/            # 核心模块
│   │   ├── config.py        # 配置管理
│   │   └── llm_client.py    # LLM 客户端
│   ├── services/            # 业务服务
│   │   ├── session_manager.py # 会话管理
│   │   └── file_processor.py  # 文件处理
│   ├── workflow/            # LangGraph 工作流
│   │   ├── state.py         # 状态定义
│   │   ├── graph.py         # 协调型编排
│   │   └── bid_build_graph.py # A→E 干运行工作流
│   ├── pyproject.toml       # Python项目配置
│   └── main.py              # 应用入口
├── frontend/               # Next.js 前端
│   ├── app/               # App Router
│   ├── components/        # React 组件
│   │   ├── ChatPanel.tsx  # 聊天面板
│   │   ├── FileTree.tsx   # 文件树
│   │   └── MarkdownEditor.tsx # 编辑器
│   ├── hooks/             # 自定义 hooks
│   │   ├── useChat.ts     # 聊天钩子
│   │   └── useSession.ts  # 会话钩子
│   └── package.json       # 前端依赖
├── uploads/               # 文件上传目录
├── wiki/                  # 文档解析结果
└── CLAUDE.md             # Claude Code 指南
```

## API 接口

### 聊天接口
```http
POST /api/v1/chat/message
Content-Type: application/json

{
  "session_id": "uuid-string",
  "message": "处理这份招标文件",
  "uploaded_files": [...]
}
```

### 文件上传接口
```http
POST /api/v1/files/upload
Content-Type: multipart/form-data

files: [file1, file2, ...]
```

### 会话管理接口
```http
GET /api/v1/sessions/{session_id}
POST /api/v1/sessions/create
DELETE /api/v1/sessions/{session_id}
```

### 投标构建接口（A→E 干运行）
```http
POST /api/v1/proposals/build
Content-Type: application/json

{
  "session_id": "uuid-string",
  "uploaded_files": [
    {
      "name": "招标文件.md",
      "type": "text/markdown",
      "content": "# 第四章 技术规格书...\n# 第五章 投标文件格式..."
    }
  ],
  "wiki_dir": "wiki",
  "meta": {"project_name": "某某项目"}
}
```

返回字段：
- `outline_path`: 生成的 `wiki/投标文件_骨架.md`
- `spec_path`: 生成的 `wiki/技术规格书_提取.md`
- `plan_path`: 生成的 `wiki/方案_提纲.md`
- `draft_path`: 生成的 `wiki/投标文件_草案.md`
- `sanity_report`: 一致性/缺项检查摘要
- `sanity_report_path`: `wiki/sanity_report.json`

前端三面板建议：
- 左侧：文件树指向 `wiki/`
- 中间：打开 `wiki/投标文件_草案.md`
- 右侧：调用 `/api/v1/proposals/build` 触发 A→E 干运行

## 开发指南

### 代码质量
```bash
# Python 代码检查
cd backend && ruff check . && ruff format .

# 前端代码检查
cd frontend && npm run lint

# TypeScript 类型检查
cd frontend && npx tsc --noEmit
```

### 环境检查
```bash
# 后端环境检查
cd backend && python check_env.py

# 前端环境检查
cd frontend && node check-env.js
```

### 扩展开发

#### 添加新智能体
1. 继承 `BaseAgent` 类
2. 实现 `execute` 和 `get_system_prompt` 方法
3. 在 `llm_client.py` 中添加模型配置
4. 在协调智能体中注册新智能体

#### 添加新LLM提供商
1. 在 `LLMProvider` 枚举中添加新提供商
2. 实现对应的客户端类
3. 在工厂方法中注册新客户端

## 故障排除

### 常见问题

**API Key 未配置**
- 检查 `.env` 文件中的 API key
- 确保环境变量正确加载

**文件上传失败**
- 检查文件大小限制 (默认50MB)
- 确保上传目录权限正确

**前端无法连接后端**
- 确认后端运行在 8001 端口
- 检查 CORS 设置

### 获取 API 密钥

- **OpenRouter**: https://openrouter.ai/keys
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/

## 许可证

MIT License

## 支持

如有问题或建议，请提交 Issue。