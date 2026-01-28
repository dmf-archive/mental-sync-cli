# Anamnesis: 记忆-任务时间线分离与自适应回想架构

> "We don't need time travel (D-Mail); we just need to remember the future we discarded, and compress it into wisdom."

## 1. 核心理念：DreamCoder 的微缩影

在传统的 Agent 框架中，回滚（Rollback）往往意味着信息的丢失。**Anamnesis (回想)** 架构不仅是一种记忆保留机制，更是 **DreamCoder** 理念在单次任务中的微缩实现。

当 Agent 决定回滚时，它进入了一个微型的“睡眠/抽象”阶段：将具体的、失败的执行轨迹（Wake Phase），抽象为通用的知识与策略（Sleep Phase），从而实现自我进化。

## 2. 架构定义

### 2.1 双重时间线

1. **Task Event Stream (任务事件流 / World State)**:
   - **定义**: 任务执行的逻辑步骤序列（Step 1 -> Step 2 -> Step 3）。
   - **性质**: **可逆（Reversible）**。
   - **操作**: Agent 调用 `jump_to_step(step_id)` 触发物理环境回滚。

2. **Operation Stream (操作行为流 / Agent Context)**:
   - **定义**: Agent 的思考、工具调用、观察结果的线性序列。
   - **性质**: **单向递增（Monotonic）**。
   - **关键特性**: 即使 World State 回滚，Agent 对“已废弃未来”的记忆**完整保留**，直到触发压缩。

### 2.2 EAS (Effective Attention Span) 机制

为了防止 Operation Stream 过长导致模型注意力“摊平”或陷入死循环，系统引入 **EAS 监控协议**：

- **EAS 表**: 由 `Reflect-Agent`通过多维度调查（在线评论？历史工作记录？）和人类操作员动态维护，记录各模型的真实有效注意力区间（例如：Gemini-3-Pro 标称 1M，但 EAS 可能仅为 64k）。
- **触发条件**: 当发生回滚且废弃片段的 Token 数超过 EAS 阈值时，强制触发 Anamnesis 过程。

## 3. 交互机制：Anamnesis 双重产出协议

当 Anamnesis 被触发时，系统不仅仅是压缩上下文，而是产生**两种**截然不同的产物：

### 3.1 Hot Memory: 上下文压缩摘要 (Context Summary)

- **目的**: 服务于**当前会话**，防止死循环，维持短期操作连贯性。

- **存储位置**: 当前 Agent 的 Context Window。
- **内容**:
  - `[ANAMNESIS_BLOCK]`: 包含核心失败原因、已证伪的路径、关键调试发现。
  - *作用*: 像路标一样告诉 Agent：“这条路刚才走过了，不通。”

### 3.2 Cold Knowledge: 知识点卡片 (Bullet Knowledge Point Card)

- **目的**: 服务于**长期记忆**，实现跨任务/跨会话的知识复用（DreamCoder 的 Abstraction）。

- **存储位置**: 全局 RAG 向量数据库 (`knowledge_base/`)。
- **格式**: 结构化的 Markdown 卡片。

    ```markdown
    ---
    type: knowledge_card
    topic: "Python Circular Import"
    source_task: "task_123_fix_auth"
    ---
    - **Issue**: 在 `auth.py` 中引入 `user.py` 导致循环依赖。
    - **Solution**: 使用 `TYPE_CHECKING` 块或延迟导入。
    - **Constraint**: 现有架构严禁在模块顶层进行双向引用。
    ```

- **作用**: 当未来其他 Agent 遇到类似场景时，通过 RAG 检索出这张卡片，避免重蹈覆辙。

## 4. 行为约束与策略

- **调研优先 (Research-First)**: 针对来源混杂的 API/Model，Agent 必须先执行 `investigate` 行为，验证环境约束，而非盲目执行。
- **对抗死循环**: 若同一 `step_id` 发生超过 3 次回滚，系统将强制介入并要求 `Reflect-Agent` 重新评估当前策略。

## 5. 流程可视化

```mermaid
graph TD
    A[label("Step 1: Success")] --> B[label("Step 2: Success")]
    B --> C[label("Step 3: Failure Detected")]
    C --> D[label("Anamnesis Triggered (Sleep Phase)")]
    D --> E[label("Generate Hot Memory (Summary)")]
    D --> F[label("Generate Cold Knowledge (RAG Card)")]
    E --> G[label("Inject into Context")]
    F --> H[label("Store in RAG DB")]
    G --> I[label("Rollback World State to Step 2")]
    I --> J[label("Step 2 Retry 1 (Wake Phase)")]
```

## 6. 总结

Anamnesis 协议通过区分“热记忆”与“冷知识”，完美解决了短期上下文限制与长期能力积累的矛盾。它将每一次失败都转化为系统的永久资产，正如 DreamCoder 所展示的那样：**我们通过记住并抽象被废弃的未来，来构建更强大的现在。**
