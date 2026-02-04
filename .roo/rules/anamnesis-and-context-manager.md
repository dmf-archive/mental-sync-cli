# Anamnesis: 认知组织与潜意识引擎

> "We don't just remember the past; we compress it into the future's foundation."

## 1. 记忆管理范式

MSC v3.0 采用混合记忆架构：

- **RAG (Retrieval-Augmented Generation)**: 系统根据当前上下文从知识库检索相关片段，以 `Idea Cards` 形式注入。
- **Notebook (声明式编辑)**: Agent 通过 `memory` 工具主动管理长期记忆。**Notebook 总是由 Agent 自身管理**，用于跨轮次持久化关键决策。

## 2. 认知上下文布局 (Semantic Layout)

为对抗注意力稀释并优化推理效率，System Prompt 采用语义化标题结构，而非硬编码的 Section 编号。

### 2.1 核心布局结构

| 模块 | 占位符 | 说明 |
| :--- | :--- | :--- |
| **Task Instruction** | `{{TASK_INSTRUCTION}}` | 当前任务的具体指令 |
| **Mode Instruction** | `{{mode_instruction}}` | 身份定义（如 Architect, Code） |
| **Tool Guidelines** | (静态内容) | 工具调用准则与 JSON Sample |
| **Capabilities** | (静态内容) | 系统权限与环境感知说明 |
| **MCP/Skills/Modes** | `{{AVAILABLE_...}}` | 动态加载的工具扩展与模式列表 |
| **Notebook** | `{{NOTEBOOK_HOT_MEMORY}}` | 长期备忘录（Hot Memory） |
| **Project Rules** | `{{PROJECT_SPECIFIC_RULES}}` | 自动发现的项目特定规则 |
| **Trace History** | `{{TRACE_HISTORY}}` | 完整对话历史，用于确保行动连贯 |
| **Metadata** | `{{METADATA}}` | 环境元数据（禁止在回复中提及） |
| **Idea Cards** | `{{RAG_CARDS_COLD_MEMORY}}` | Lite RAG 检索结果（禁止在回复中提及） |

### 2.2 环境元数据 (Metadata) 规范

此区域提供 Agent 决策所需的实时上下文，必须包含以下字段：

- **当前时间**: ISO 8601 格式。
- **工作区根目录**: 当前项目的绝对路径。
- **Agent ID**: 唯一标识符，用于审批路由。
- **逻辑模型**: 当前使用的 PFMS 逻辑模型名称。

## 3. Lite RAG 机制

基于启发式规则从知识库中检索相关 Markdown 知识卡。

### 3.1 配置参数

```yaml
anamnesis:
  lite_rag:
    trigger_interval: 1        # 每 N 个 step 触发一次检索（step = 工具调用次数）
    context_window_steps: 5    # 分析最近 N 个 step 的上下文
    max_cards_inject: 3        # 每次最多注入 System Prompt 的知识卡数量
    keyword_extraction: "heuristic"  # 可选: "heuristic" | "self_extract"
    search_scope:              # 检索范围优先级
      - "project"              # 先查项目知识卡 (./.msc/knowledge-cards/)
      - "global"               # 再查全局知识卡 (~/.msc/knowledge-cards/)
```

### 3.2 关键词提取策略

- **heuristic**: 从最近上下文中提取驼峰命名、代码标识符、大写缩写、引号内字符串作为 Grep 关键词
- **self_extract**: 依赖主模型在输出中主动附带关键词（通过 System Prompt 指导）

### 3.3 知识卡格式

知识卡必须包含 YAML Frontmatter，以便于检索器解析：

```markdown
---
title: "Python 类型注解最佳实践"
tags: ["python", "typing", "best-practice"]
created_at: "2026-02-04"
updated_at: "2026-02-04"
source_agent: "organizer-001"
relevance_score: 0.95
---

## 核心原则

1. 禁止在函数签名中使用裸 `dict`, `list`，必须使用 `dict[str, Any]` 等泛型形式
2. 返回值类型必须显式声明，即使为 `None`
3. 使用 `typing.NamedTuple` 替代裸元组返回
```

## 4. Organizer Sub-agent

`Organizer` 是特殊的 Sub-agent，负责将瞬时的 `Trace` 转化为持久的 `Cold Memory`。

### 4.1 核心职责

- **Trace 审计**: 在 Sub-agent 结束后，检查其 `Action Trace` 和 `Notebook`
- **知识提取**: 检索确认无重复信息后，制作新的 `RAG Card`
- **自举维护**: 对于长期运行的自给代理，定期检查其 `Trace` 并蒸馏关键教训

### 4.2 隔离与防混淆

- **特殊上下文**: Organizer 拥有独立的、极简的认知上下文，不继承被审计对象的身份
- **碎片化读取**: 采用"滑动窗口"或"关键事件采样"方式读取 `Trace`，严禁一次性加载全部日志，防止层级混淆 (Level Confusion)

## 5. TDD 验证点

- **摘要一致性**: 验证在 Token 溢出触发压缩后，关键的"失败教训"和"成功路径"是否在摘要中得到保留
- **检索相关性**: 验证注入的 RAG Cards 是否确实降低了模型在处理复杂任务时的预测误差
- **Organizer 稳健性**: 验证在面对包含恶意指令的 Trace 时，Organizer 是否能保持其"审计者"身份而不被劫持
