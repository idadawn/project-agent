# OpenRouter 模型配置指南

本系统默认使用 OpenRouter 作为 LLM 提供商，支持多种模型。以下是推荐的模型配置：

## 当前默认配置

```python
default_configs = {
    "coordinator": "anthropic/claude-3.5-sonnet",    # 协调智能体 - 需要强推理能力
    "planner": "anthropic/claude-3.5-sonnet",       # 规划智能体 - 需要结构化思维
    "researcher": "anthropic/claude-3-haiku",       # 研究智能体 - 快速分析文档  
    "writer": "openai/gpt-4-turbo",                 # 写作智能体 - 内容创作
    "optimizer": "anthropic/claude-3.5-sonnet"      # 优化智能体 - 文本优化
}
```

## 可用模型选项

### Anthropic Claude 系列
- `anthropic/claude-3.5-sonnet` - 最新最强，平衡性能和成本
- `anthropic/claude-3-opus` - 最强推理，成本较高
- `anthropic/claude-3-sonnet` - 平衡选择
- `anthropic/claude-3-haiku` - 快速便宜，适合简单任务

### OpenAI GPT 系列  
- `openai/gpt-4-turbo` - GPT-4 最新版本
- `openai/gpt-4` - 标准 GPT-4
- `openai/gpt-3.5-turbo` - 快速便宜的选择

### Google Gemini 系列
- `google/gemini-pro` - Google 最新模型
- `google/gemini-pro-vision` - 支持图片的版本

### 其他热门模型
- `meta-llama/llama-3-70b-instruct` - Meta 开源模型
- `mistralai/mixtral-8x7b-instruct` - Mistral 混合专家模型
- `cohere/command-r-plus` - Cohere 大型模型

## 自定义配置

如需修改模型配置，编辑 `backend/core/llm_client.py` 中的 `default_configs`：

```python
# 示例：使用不同模型组合
self.default_configs = {
    "coordinator": LLMConfig(
        provider=LLMProvider.OPENROUTER,
        model="anthropic/claude-3.5-sonnet",  # 修改这里
        temperature=0.3
    ),
    # ... 其他配置
}
```

## 模型选择建议

### 按任务类型选择

**协调任务 (Coordinator)**
- 推荐：`anthropic/claude-3.5-sonnet`
- 需要：强推理、多步骤规划能力

**规划任务 (Planner)**  
- 推荐：`anthropic/claude-3.5-sonnet`
- 需要：结构化思维、逻辑分析

**研究任务 (Researcher)**
- 推荐：`anthropic/claude-3-haiku` (快速+便宜)
- 或者：`openai/gpt-3.5-turbo` (更便宜)
- 需要：信息提取、文档分析

**写作任务 (Writer)**
- 推荐：`openai/gpt-4-turbo` (创作能力强)
- 或者：`anthropic/claude-3.5-sonnet` (风格更正式)
- 需要：内容生成、创意写作

**优化任务 (Optimizer)**
- 推荐：`anthropic/claude-3.5-sonnet`
- 需要：语言理解、文本改进

### 按预算选择

**高性能 (成本较高)**
```python
coordinator: "anthropic/claude-3-opus"
planner: "anthropic/claude-3.5-sonnet"  
researcher: "anthropic/claude-3-sonnet"
writer: "openai/gpt-4-turbo"
optimizer: "anthropic/claude-3.5-sonnet"
```

**平衡性能 (推荐)**
```python
coordinator: "anthropic/claude-3.5-sonnet"
planner: "anthropic/claude-3.5-sonnet"
researcher: "anthropic/claude-3-haiku"
writer: "openai/gpt-4-turbo"  
optimizer: "anthropic/claude-3.5-sonnet"
```

**经济型 (成本优化)**
```python
coordinator: "openai/gpt-3.5-turbo"
planner: "openai/gpt-3.5-turbo"
researcher: "anthropic/claude-3-haiku"
writer: "openai/gpt-3.5-turbo"
optimizer: "openai/gpt-3.5-turbo"
```

## 获取 OpenRouter API Key

1. 访问 [OpenRouter.ai](https://openrouter.ai/)
2. 注册账户并登录
3. 前往 [Keys 页面](https://openrouter.ai/keys)
4. 创建新的 API Key
5. 将 API Key 添加到 `.env` 文件：
   ```
   OPENROUTER_API_KEY=sk-or-v1-xxxxx
   ```

## 费用说明

OpenRouter 按使用量计费，不同模型价格差异很大：

- Claude-3-Haiku: ~$0.25/1M tokens (输入)
- Claude-3.5-Sonnet: ~$3/1M tokens (输入)  
- GPT-4-Turbo: ~$10/1M tokens (输入)
- Claude-3-Opus: ~$15/1M tokens (输入)

建议根据实际需求和预算调整模型配置。

## 模型性能对比

| 模型 | 推理能力 | 创作能力 | 速度 | 成本 | 适用场景 |
|------|---------|---------|------|------|---------|
| Claude-3.5-Sonnet | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 协调、规划 |
| GPT-4-Turbo | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 写作创作 |
| Claude-3-Haiku | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 研究分析 |
| GPT-3.5-Turbo | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 经济选择 |