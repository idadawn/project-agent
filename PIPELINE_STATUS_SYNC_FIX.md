# 前端智能体流水线状态同步问题修复

## 问题分析

用户反馈了一个严重的状态同步问题：后端已经完成所有工作并生成了文件，但前端的智能体执行流水线状态仍然停留在第1步。

### 根本原因

经过代码分析，发现问题的根源是**前端智能体名称映射不一致**：

#### 后端发送的智能体名称（API输出）：
- `coordinator`
- `DocumentParserAgent` 
- `StructureExtractor`
- `SpecExtractor`
- `PlanOutliner`
- `BidAssembler`
- `SanityChecker`

#### 前端期望的agentKey：
- `coordinator`
- `structure_extractor`
- `spec_extractor`
- `plan_outliner`
- `bid_assembler`
- `sanity_checker`

由于名称不匹配，前端无法正确识别当前执行的步骤，导致流水线进度始终停留在第一步。

## 修复方案

### 1. 添加智能体名称映射函数

在ChatPanel组件中新增 `mapAgentNameToKey` 函数，将后端发送的智能体名称映射到前端的agentKey：

```typescript
const mapAgentNameToKey = (backendAgentName: string): string => {
  const agentMapping: Record<string, string> = {
    'coordinator': 'coordinator',
    'document_parser': 'coordinator', // 文档解析阶段也显示为第一步
    'DocumentParserAgent': 'coordinator',
    'StructureExtractor': 'structure_extractor',
    'SpecExtractor': 'spec_extractor', 
    'PlanOutliner': 'plan_outliner',
    'BidAssembler': 'bid_assembler',
    'SanityChecker': 'sanity_checker',
    // 添加小写版本的映射
    'structure_extractor': 'structure_extractor',
    'spec_extractor': 'spec_extractor',
    'plan_outliner': 'plan_outliner', 
    'bid_assembler': 'bid_assembler',
    'sanity_checker': 'sanity_checker'
  }
  return agentMapping[backendAgentName] || backendAgentName
}
```

### 2. 改进状态推断逻辑

新增 `inferPipelineStateFromMessages` 函数，更智能地从消息历史中推断流水线状态：

```typescript
const inferPipelineStateFromMessages = () => {
  // 从最新消息开始向前查找
  for (let i = messages.length - 1; i >= Math.max(0, messages.length - 3); i--) {
    const message = messages[i]
    if (message.role !== 'assistant') continue
    
    const content = message.content || ''
    const metadata = message.metadata || {}
    
    // 检查是否是完成状态
    if (content.includes('✅ 已完成A–E链路') || 
        metadata.stage === 'bid_build_completed') {
      return {
        agent: 'sanity_checker', // 最后一步是完整性校验
        status: 'completed',
        action: 'bid_build_completed'
      }
    }
    
    // 检查具体的智能体执行状态
    if (metadata.current_agent) {
      const mappedAgent = mapAgentNameToKey(metadata.current_agent)
      let status = 'running'
      if (content.includes('✅') || content.includes('已完成')) {
        status = 'completed'
      }
      
      return { agent: mappedAgent, status, action: metadata.action || '正在执行' }
    }
  }
  return null
}
```

### 3. 重构渲染逻辑

更新 `renderTimelinePipelineProgress` 函数，优先使用实时状态，然后从消息历史推断：

```typescript
const renderTimelinePipelineProgress = (currentAgent?: string, agentStatus?: AgentStatus) => {
  // 优先使用实时状态，然后从消息历史推断
  let finalState = null
  
  if (currentAgent && agentStatus) {
    const mappedAgent = mapAgentNameToKey(currentAgent)
    finalState = {
      agent: mappedAgent,
      status: agentStatus.action === 'bid_build_completed' ? 'completed' : 'running',
      action: agentStatus.action
    }
  } else {
    // 从消息历史推断
    finalState = inferPipelineStateFromMessages()
  }
  
  if (!finalState) return null
  
  const { agent: mappedAgentKey, status, action } = finalState
  // ... 后续渲染逻辑
}
```

### 4. 添加调试信息

在前端useChat和ChatPanel中添加调试日志，帮助排查状态同步问题：

```typescript
// useChat.ts中
case 'agent_status': {
  console.log('Received agent_status:', parsed)  // 新增调试信息
  setAgentStatus({ agent: parsed.agent, action: parsed.action })
  break
}

// ChatPanel.tsx中  
console.log('Pipeline Debug:', {
  currentAgent,
  agentStatus,
  finalState,
  mappedAgentKey
})
```

## 修复效果

### 修复前：
- 后端执行完成A-E工作流的所有步骤
- 前端流水线进度停留在第1步
- 状态映射失败，无法正确显示执行进度

### 修复后：
- 前端能正确识别后端发送的智能体状态
- 流水线进度准确反映实际执行状态
- 能显示正确的步骤进度（1/6 → 2/6 → ... → 6/6）
- 完成状态能正确显示为"所有步骤已完成"

## 技术要点

1. **名称映射一致性**：确保前后端智能体名称映射的一致性
2. **状态推断增强**：从消息历史中智能推断执行状态
3. **调试信息完善**：添加详细的调试日志便于问题排查
4. **向后兼容**：支持多种命名格式的兼容性映射

## 验证方法

1. 打开浏览器开发者工具控制台
2. 上传招标文件触发A-E工作流
3. 观察控制台中的调试信息：
   - 查看 `Received agent_status:` 日志中的后端状态
   - 查看 `Pipeline Debug:` 日志中的映射结果
4. 确认流水线进度条能正确推进到各个步骤

这个修复解决了前后端状态同步的核心问题，确保用户能准确看到智能体执行流水线的实时进度。