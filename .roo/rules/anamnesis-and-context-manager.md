# Anamnesis: 认知组织与潜意识引擎

> "We don't just remember the past; we compress it into the future's foundation."

## 1. 记忆管理范式

MSC v3.0 采用混合记忆架构：

- **RAG (Retrieval-Augmented Generation)**: 系统根据当前上下文从知识库检索相关片段。
- **Notebook (声明式编辑)**: Agent 通过 `memory_add/replace/del` 工具主动管理长期记忆。**Notebook 总是由 Agent 自身管理**。

## 2. 认知上下文布局 (8-Section Layout)

为对抗注意力稀释，System Prompt 采用标准化结构：

| Section | 内容 | 更新频率 |
| :--- | :--- | :--- |
| 1. Task Instruction | 用户或父 Agent 分配的具体指令 | 每任务 |
| 2. Core Base Template | 工具调用规范与行为准则 | 全局固定 |
| 3. Notebook (Hot Memory) | Agent 自我管理的持久化记忆 | 低频 |
| 4. Project Rules (AGENTS.md) | 递归读取的项目规则集 | 中频 |
| 5. Trace History (Part 1) | 历史对话（缓存优化） | 每轮+1 |
| 6. Trace History (Part 2) | 最新用户输入 | 每轮 |
| 7. Metadata | 环境元数据（时间、目录树、系统状态） | 每轮 |
| 8. RAG Cards (Cold Memory) | Lite RAG 检索的知识卡 | 每 N step |

### 2.1 变量标签说明

| 占位符 | 类型 | 说明 |
| :--- | :--- | :--- |
| `TASK_INSTRUCTION` | VAR | 用户或父 Agent 分配的具体指令 |
| `CORE_BASE_TEMPLATE` | CONST | 行为准则与工具定义 |
| `NOTEBOOK_HOT_MEMORY` | VAR | Agent 自我管理的持久化记忆，仅 Main_Agent |
| `PROJECT_SPECIFIC_RULES` | VAR | 递归读取的 AGENTS.md 规则集 |
| `TRACE_HISTORY_PART1` | VAR | 历史对话（缓存优化） |
| `TRACE_HISTORY_PART2` | VAR | 最新用户输入 |
| `DYNAMIC_METADATA` | VAR | 环境状态快照 |
| `RAG_CARDS_COLD_MEMORY` | VAR | Lite RAG 检索结果 |

### 2.2 环境元数据 (Section 7: Metadata) 规范

此区域提供 Agent 决策所需的实时上下文，必须包含以下字段：

- **当前时间**: ISO 8601 格式，包含时区。
- **工作区根目录**: 当前项目的绝对路径。
- **活动终端**: 正在运行的进程列表及其状态。
- **资源限制**: 当前沙箱的 CPU/内存配额及剩余量。
- **Agent 身份**: `agent_id`, `parent_id` (如有), `capabilities` (如 green-tea)。
- **PFMS 状态**: 当前逻辑模型名称及 Provider 成本元数据。

### 2.3 使用说明

1. **Main Agent**: Notebook 持久化跨 Session，由 Organizer 定期蒸馏。
2. **Sub-agent**: Notebook 仅作为 Trace 临时字段，随进程回收。
3. **Token 管理**: Anamnesis 监控总 Token，触发压缩时优先压缩 Trace History。

## 3. Lite RAG 机制

基于启发式规则或主模型自提取的关键词，从全局+项目知识库中 Grep 检索相关 Markdown 知识卡。

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

知识卡以 Markdown 文件存储，YAML Frontmatter 承载元数据：

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

## 5. MCP 主动检索层 (可选)

Anamnesis 可作为独立 MCP Server 部署，提供主动知识检索能力：

- **定位**: 非 Agent Core 必需，独立项目
- **功能**: 指定 `/path` 后，管理该路径下所有 Markdown 知识卡
- **接口**: 标准 MCP Tool，支持深度检索、知识卡 CRUD

## 6. TDD 验证点

- **摘要一致性**: 验证在 Token 溢出触发压缩后，关键的"失败教训"和"成功路径"是否在摘要中得到保留
- **检索相关性**: 验证注入的 RAG Cards 是否确实降低了模型在处理复杂任务时的预测误差
- **Organizer 稳健性**: 验证在面对包含恶意指令的 Trace 时，Organizer 是否能保持其"审计者"身份而不被劫持
