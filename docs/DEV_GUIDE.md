# 开发指南（A→E Pipeline）

> 日期：2025-08-28

## 1. 目标与产物

- 目标：把“招标文件”自动转成“投标文件骨架/方案/草案”，并进行合规快检
- 产物：
  - wiki/投标文件_骨架.md
  - wiki/技术规格书_提取.md
  - wiki/方案_提纲.md
  - wiki/投标文件_草案.md
  - wiki/sanity_report.json

## 2. LangGraph 流水线

```
Uploader → Parser(已有)
        → A.StructureExtractor
        → B.SpecExtractor
        → C.PlanOutliner
        → D.BidAssembler
        → E.SanityChecker
```

### State（示例）

```python
class BidState(TypedDict, total=False):
    session_id: str
    tender_path: str
    wiki_dir: str
    meta: dict
    outline_sections: list[str]
    outline_path: str
    spec_path: str
    plan_path: str
    draft_path: str
    sanity_report_path: str
```

### 编排调用

```python
from backend.workflow.bid_graph import run_build
run_build("demo", "uploads/招标文件.md", "wiki", {"project_name":"示例项目"})
```

## 3. 结点说明

### A) StructureExtractor

- 解析“第五章 投标文件格式”→ 生成目录骨架；抽不到回退 11 项标准目录
- 归一化常见近义项：方案详细说明及施工组织设计、商务和技术偏差表等

### B) SpecExtractor

- 从“第四章 技术规格书/技术要求”到“第五章/投标文件格式”前切片
- 抽不到时输出 checklist 版规格书提纲

### C) PlanOutliner

- 把评分因子映射到提纲（技术方案25 + 施工方法及主要技术措施25）
- 每小节尾部“证据绑定：规格书 §x.x”占位
- LLM：`get_llm("plan_outliner").complete(prompt)`，不可用则回退默认提纲

### D) BidAssembler

- 拼装：骨架 + 方案提纲 + 规格书节选 → 草案

### E) SanityChecker

- 快检关键要素：工期/里程碑/第三方检测/验收/环保/安全/资料交付/质量标准/偏差表
- 输出 JSON 报告，前端可提示

## 4. Coordinator 对话建议

- 触发词：生成投标/更新投标/build/a2e/上传成功等
- 播报模板：
  1) 🧭 切换到 A→E 流程
  2) 🚀 A… → 🔎 B… → 📝 C… → 🧩 D… → ✅ E…
  3) 列出 4+1 产物的可点击路径

## 5. 前端集成

- 文件树展示 wiki/；默认打开 `投标文件_草案.md`
- “重新生成”按钮 → POST `/api/v1/proposals/build`
- 聊天面板显示阶段播报（可通过 invoke_node 分步）

## 6. 模型与上下文

- `plan_outliner` 读取 `技术规格书_提取.md` 前 12k 字，避免超长上下文
- 提纲只列结构与 checklist，后续生成写作更稳

## 7. 测试与质量

```bash
# 后端质量
cd backend && ruff check . && ruff format .

# 前端质量
cd frontend && npm run lint && npx tsc --noEmit
```

## 8. 常见问题

- 旧文案不变：重启后端与会话；更新 Coordinator 系统提示；改 ChatPanel 固定文案
- 章节抽取失败：启用目录驱动与默认模板回退
- 只想更新方案：只重跑 C/D/E 节点

## 9. 扩展

- F. DiffTableBuilder：自动生成偏差表（无偏差输出“无”）
- G. FinalQA：评分映射与条款逐点校验报告