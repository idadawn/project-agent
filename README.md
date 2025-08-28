# Project Agent – 投标文件生成系统（A→E Pipeline）

> FastAPI + LangGraph + Next.js 的多智能体投标文件处理与生成系统  
> **已切换为 A→E 流程**：A 结构抽取 → B 规格书提取 → C 方案提纲 → D 拼装草案 → E 合规校验

## ✨ 特性

- 多智能体编排（LangGraph）：新增 A→E 五结点
- 强鲁棒结构抽取：不规整文档也能回退到 11 项标准骨架
- 规格书精准抽取：自动切片“第四章 技术规格书/技术要求”→“第五章/投标文件格式”前
- 与评分对齐的方案提纲：技术方案 25 分 + 施工方法及主要技术措施 25 分
- 一键拼装草案：骨架 + 方案提纲 + 规格书节选
- 合规快检：工期/环保/安全/第三方检测/资料交付/验收等关键项缺失提示
- 三面板界面：文件树（wiki/）+ Markdown 编辑器 + 聊天（Coordinator）

## 🧭 新流程（A→E）

1. A · StructureExtractor → 生成 `wiki/投标文件_骨架.md`
2. B · SpecExtractor → 生成 `wiki/技术规格书_提取.md`
3. C · PlanOutliner → 生成 `wiki/方案_提纲.md`
4. D · BidAssembler → 生成 `wiki/投标文件_草案.md`
5. E · SanityChecker → 生成 `wiki/sanity_report.json`

> 兼容“每份都不一样”：**标题匹配 → 目录驱动 → 默认模板** 三层兜底。

## 🚀 快速开始

### 环境

- Python 3.11+ · Node.js 18+ · `uv`（可选）

### 安装

```bash
# 后端
cd backend
uv venv --python 3.11 && uv sync
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 前端
cd ../frontend && npm install
```

### 配置（.env）

```bash
OPENROUTER_API_KEY=sk-or-v1-***
# 可选：
OPENAI_API_KEY=sk-***
ANTHROPIC_API_KEY=sk-***
SECRET_KEY=your-secret-key
```

### 启动

```bash
# 后端
cd backend && python dev.py   # http://localhost:8001

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
- 若聊天仍显示旧文案“1→2→3”：请更新 `coordinator.py` 的系统提示与触发逻辑（详见开发指南）。

## 📁 目录结构（关键）

```
project-agent/
├── backend/
│   ├── agents/
│   │   ├── structure_extractor.py
│   │   ├── spec_extractor.py
│   │   ├── plan_outliner.py
│   │   ├── bid_assembler.py
│   │   └── sanity_checker.py
│   ├── prompts/plan_outliner.md
│   ├── workflow/bid_graph.py
│   └── api/v1/endpoints/proposals.py
├── uploads/         # 输入
└── wiki/            # 输出
```

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

## 🧯 故障排除

- 会话提示没变：重启后端；清空旧会话缓存；改前端固定文案  
- 抽不到章节：自动回退；建议 Parser 统一标题层级  
- 不刷新 wiki/：生成后刷新文件树或前端主动打开草案

## 📜 许可证

MIT