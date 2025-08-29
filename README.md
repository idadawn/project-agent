# Project Agent – 智能投标文件生成系统（文档解析 → A-E Pipeline）
> FastAPI + LangGraph + Next.js 的多智能体投标文件处理与生成系统  
> **完整 6 步流程**：文档解析 → A 结构抽取 → B 规格书提取 → C 方案提纲 → D 拼装草案 → E 合规校验

## ✨ 特性
- 多智能体编排（LangGraph）：文档解析 + A→E 六结点
- 文档解析：使用 microsoft/markitdown 将 PDF/DOCX 转为 Markdown
- 强鲁棒结构抽取：不规整文档也能回退到 11 项标准骨架
- 规格书精准抽取：自动切片“第四章 技术规格书/技术要求”→“第五章/投标文件格式”前
- 与评分对齐的方案提纲：技术方案 25 分 + 施工方法及主要技术措施 25 分
- 一键拼装草案：骨架 + 方案提纲 + 规格书节选
- 合规快检：工期/环保/安全/第三方检测/资料交付/验收等关键项缺失提示
- 三面板界面：文件树（wiki/）+ Markdown 编辑器 + 聊天（Coordinator）
- 智能体Pipeline可视化：实时显示执行进度和状态

## 🧭 完整 6 步工作流（文档解析 → A-E Pipeline）
0. **文档解析** · DocumentParserAgent → 生成 `uploads/原文件` + `wiki/招标文件.md`
1. **A · 结构抽取** · StructureExtractor → 生成 `wiki/投标文件_骨架.md`
2. **B · 规格书提取** · SpecExtractor → 生成 `wiki/技术规格书_提取.md`
3. **C · 方案提纲生成** · PlanOutliner → 生成 `wiki/方案_提纲.md`
4. **D · 投标草案拼装** · BidAssembler → 生成 `wiki/投标文件_草案.md`
5. **E · 完整性校验** · SanityChecker → 生成 `wiki/合规性报告.json`

> 📝 **新增亮点**：自动识别Word/PDF文件上传，触发智能体Pipeline可视化界面，实时显示执行进度。  
> 兼容“每份都不一样”：**标题匹配 → 目录驱动 → 默认模板** 三层兜底。

## 🚀 快速开始

### 环境要求
- Python 3.11+ · Node.js 18+ · `uv`（可选）

### 安装依赖
```bash
# 后端
cd backend && python -m pip install -r requirements.txt
# 或使用 uv: uv sync

# 前端
cd frontend && npm install
```

### 配置环境变量
在 `backend/.env` 中配置：
```bash
OPENROUTER_API_KEY=sk-or-v1-***
# 可选：
OPENAI_API_KEY=sk-***
ANTHROPIC_API_KEY=sk-***
SECRET_KEY=your-secret-key
```

### 启动服务
```bash
# 后端（在项目根目录）
python dev.py   # http://localhost:8001

# 前端
cd frontend && npm run dev    # http://localhost:3000
```

## 📡 一键生成（API）
```http
POST /api/v1/proposals/build
Content-Type: application/json

{
  "session_id": "demo",
  "tender_path": "uploads/招标文件.md",
  "wiki_dir": "wiki",
  "meta": {"project_name": "示例项目"}
}
```
返回：`投标文件_骨架.md` · `技术规格书_提取.md` · `方案_提纲.md` · `投标文件_草案.md` · `sanity_report.json`

## 💬 与 Coordinator 对话（可选）
- 口令示例：**使用 A→E 流程生成投标文件（源=uploads/招标文件.md，项目=×××）**
- 若聊天仍显示旧文案"1→2→3"：请更新 `coordinator.py` 的系统提示与触发逻辑（详见开发指南）。

## 📁 目录结构（关键）
```
project-agent/
├── backend/
│   ├── agents/
│   │   ├── document_parser.py      # 文档解析智能体
│   │   ├── structure_extractor.py  # A-结构抽取
│   │   ├── spec_extractor.py       # B-规格书提取
│   │   ├── plan_outliner.py        # C-方案提纲
│   │   ├── bid_assembler.py        # D-草案拼装
│   │   └── sanity_checker.py       # E-完整性校验
│   ├── api/v1/endpoints/
│   │   ├── pipeline.py             # Pipeline API端点
│   │   └── proposals.py            # 投标文件生成API
│   ├── prompts/plan_outliner.md
│   └── workflow/bid_graph.py
├── frontend/
│   ├── components/
│   │   ├── PipelinePanel.tsx       # Pipeline可视化组件
│   │   └── ChatPanel.tsx           # 聊天面板（集成Pipeline）
│   └── hooks/
│       └── usePipeline.ts          # Pipeline状态管理
├── uploads/         # 输入（原始文件）
└── wiki/            # 输出（生成文件）
```

## 🔧 技术架构

### 后端（FastAPI + LangGraph）
- **核心框架**: FastAPI + LangGraph + Pydantic
- **A→E 智能体链**:
  - `StructureExtractor`: 结构抽取，生成投标文件骨架
  - `SpecExtractor`: 规格书抽取，提取第四章技术要求
  - `PlanOutliner`: 方案提纲，生成技术方案大纲
  - `BidAssembler`: 文件拼装，整合所有组件
  - `SanityChecker`: 合规校验，检查完整性
- **LLM 支持**: OpenRouter 统一接口，支持多种模型

### 前端（Next.js 14）
- **框架**: Next.js 14 + React + TypeScript + Tailwind CSS
- **三面板布局**: 文件树 + Markdown编辑器 + 聊天面板
- **实时优化**: 支持在Markdown编辑器中实时文本优化
- **智能体Pipeline可视化**: 
  - 自动检测Word/PDF文件上传并触发Pipeline界面
  - 6步工作流实时进度追踪和状态显示
  - 支持单步执行和一键执行全流程
  - 生成的文件自动显示在左侧文件树中

## 📦 使用指南

### 1. 准备招标文件
```bash
# 创建必要目录
mkdir -p uploads wiki

# 将招标文件复制到 uploads 目录
cp 你的招标文件.md uploads/招标文件.md
```

### 2. 启动服务
```bash
# 启动后端服务
python dev.py

# 另开终端启动前端
cd frontend && npm run dev
```

### 3. 使用完整 6 步流程
有两种方式触发完整流程：

#### 方式 1：前端界面（推荐）
1. 访问 http://localhost:3000
2. 点击📎按钮上传Word或PDF招标文件
3. 系统自动检测文件类型并显示智能体Pipeline界面
4. 点击“一键执行”或逐步执行每个步骤
5. 实时查看执行进度和生成的文件

#### 方式 2：直接 API 调用
```bash
# 首先上传文件到uploads目录
cp 你的招标文件.docx uploads/

# 调用API触发完整流程
curl -X POST http://localhost:8001/api/v1/proposals/build \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo",
    "tender_path": "uploads/招标文件.md",
    "wiki_dir": "wiki",
    "meta": {"project_name": "示例项目"}
  }'
```

### 4. 查看结果
生成完成后，可在以下位置查看结果：

**uploads/ 目录**（原始文件）：
- 上传的原始招标文件（Word/PDF等）

**wiki/ 目录**（生成文件）：
- `招标文件.md` - 解析后的结构化文档（文档解析步骤）
- `投标文件_骨架.md` - 投标文件结构框架（A步）
- `技术规格书_提取.md` - 提取的技术要求（B步）
- `方案_提纲.md` - 技术方案大纲（C步）
- `投标文件_草案.md` - 最终拼装的投标文件（D步）
- `合规性报告.json` - 合规性检查报告（E步）

**前端界面**：
- 左侧文件树会自动显示所有生成的文件
- 点击文件名即可在中间的Markdown编辑器中预览和编辑

## 🧰 模型配置
```python
# backend/app_core/llm_client.py
default_configs.update({
  "plan_outliner": "anthropic/claude-3.5-sonnet"
})
# get_llm(alias).complete(prompt)->str
```

## 🧪 验证
```bash
curl -X POST http://localhost:8001/api/v1/proposals/build   -H 'Content-Type: application/json'   -d '{"session_id":"demo","tender_path":"uploads/招标文件.md","wiki_dir":"wiki","meta":{"project_name":"示例"}}'
```

## 🔧 迁移（旧 1→2→3 → 新 A→E）
1) 合入 `agents/*`、`workflow/bid_graph.py`、`api/v1/endpoints/proposals.py`  
2) 前端按钮调用 `/proposals/build` 并刷新 wiki/  
3) Coordinator 更新系统提示与触发词，分阶段播报 A→E  
4) （可选）只重跑 C/D/E 更新方案与草案

## 🚑 故障排除

### 常见问题及解决方案

**1. 会话提示还是旧流程**
- 重启后端服务：`python dev.py`
- 清空浏览器缓存和会话数据
- 检查 `coordinator.py` 的系统提示是否已更新

**2. API 返回 "404 Not Found"**
- 确认后端服务在 8001 端口运行
- 检查 API 路径：`/api/v1/proposals/build`
- 检查 CORS 设置是否允许 `http://localhost:3000`

**3. "找不到文件"错误**
- 确保 `uploads/招标文件.md` 文件存在
- 检查文件路径和权限
- 确认项目目录结构正确

**4. 抽不到章节内容**
- 系统会自动回退到默认模板
- 建议统一招标文件的标题层级（如都使用 `## 第四章`）
- 检查文件编码是否为 UTF-8

**5. 不刷新 wiki/ 目录**
- API 调用成功后手动刷新文件树
- 或前端主动打开生成的草案文件
- 检查文件写入权限

**6. LLM 调用失败**
- 检查 `.env` 中的 API 密钥配置
- 系统已内置回退机制，不会卡死
- 可先使用默认模板，后续再配置模型

### 开发调试
```bash
# 检查后端日志
tail -f backend/logs/app.log

# 手动清理缓存
rm -rf wiki/* uploads/*

# 重新初始化
mkdir -p wiki uploads
```

## 📜 许可证
MIT