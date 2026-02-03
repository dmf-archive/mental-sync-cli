# Anamnesis: 认知组织与潜意识引擎

> "We don't just remember the past; we compress it into the future's foundation."

## 1. 记忆管理范式

在 MSC v3.0 中，Agent 的记忆管理超越了简单的对话历史堆叠，采用了混合架构：

- **RAG (Retrieval-Augmented Generation)**: 类似推荐系统。系统根据当前上下文“猜你想做”，从海量知识库中检索相关片段。
- **Notebook (声明式编辑)**: 允许 Agent 调用 `memory_add`, `memory_replace`, `memory_del` 工具，像编辑笔记一样主动管理自己的长期记忆条目。**Notebook 总是由 Agent 自身管理**。

## 2. 认知上下文布局 (Context Layout)

为了对抗注意力稀释并优化推理效率，MSC 采用以下标准化的 System Prompt 布局：

1. `Task Instruction`: 用户指令或 Main Agent 分配的子任务指令。在整个任务周期内不变。
2. `Core Base Template`: 纯粹的工具调用规范与行为准则（不包含身份信息）。在整个任务周期内不变。
3. `Notebook (Hot Memory)`:
   - Main Agent: 持久化跨 Session 运作。
   - Sub-agent: 仅作为 Trace 中的临时字段，随进程回收。
   - 在整个任务周期很少变动。
4. `Trace History (Part 1)`: 历史聊天记录与工具调用日志。每轮对话稳定+1条目。和Part 2串联以尽可能提升缓存命中。
5. `Trace History (Part 2)`: 用户的最新指令。每轮变动。
6. `Metadata`: 动态环境元数据（工作区目录树、当前时间、系统状态）。每轮变动。
7. `RAG Cards (Cold Memory)`:
   - `Lite RAG 机制`: 使用廉价模型根据最近 8k 上下文生成 Grep 关键词，直接检索全局+项目特定的知识库然后填入。每轮变动。

## 3. Organizer Sub-agent: 知识蒸馏与冷启动

`Organizer` 是一个特殊的 Sub-agent，负责将瞬时的 `Trace` 转化为持久的 `Cold Memory`。

### 3.1 核心职责

- **Trace 审计**: 在 Sub-agent 结束后，检查其 `Action Trace` 和 `Notebook`。
- **知识提取**: 检索确认无重复信息后，制作新的 `RAG Card`。
- **自举维护**: 对于长期运行的自给代理 (Self-bootstrap Main-agent)，定期检查其 `Trace` 并蒸馏关键教训。

### 3.2 隔离与防混淆

- **特殊上下文**: Organizer 拥有独立的、极简的认知上下文，不继承被审计对象的身份。
- **碎片化读取**: 采用“滑动窗口”或“关键事件采样”方式读取 `Trace`，严禁一次性加载全部日志，以防止 Organizer 陷入被审计 Trace 中大量用户指令导致的层级混淆 (Level Confusion)。

## 4. 运行机制

- **实时压缩**: Anamnesis 监控会话 Token 消耗。当接近阈值时，它会将 Hot Memory 中的冗余信息抽象为摘要，并清理无效的尝试路径。
- **潜意识注入**: 在每一轮对话开始前，Anamnesis 都会根据最近的对话轨迹，从 `knowledge_base/` 中提取最相关的 RAG Cards 注入到 System Prompt 的特定区域。

## 5. TDD 验证点

- **摘要一致性**: 验证在 Token 溢出触发压缩后，关键的“失败教训”和“成功路径”是否在摘要中得到保留。
- **检索相关性**: 验证注入的 RAG Cards 是否确实降低了模型在处理复杂任务时的预测误差。
- **Organizer 稳健性**: 验证在面对包含恶意指令（Prompt Injection）的 Trace 时，Organizer 是否能保持其“审计者”身份而不被劫持。
