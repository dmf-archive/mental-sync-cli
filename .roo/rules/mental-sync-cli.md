# Mental-Sync-CLI: Engineering Reality vs. Narrative Fiction

> "Code is Law, Proof is Reality."

## 0. 引言

本项目 **Mental-Sync-CLI (MSC)** 是科幻设定集 **Web://Reflect** 的工程化投影。为了避免概念混淆，本文档旨在明确区分“故事设定”与“现实工程”的边界。

**核心声明**：
MSC **不是**脑机接口，**无法**读取神经信号，也**不具备**真正的自主意识（暂时）。它是一个**高度自动化的智能体运行时环境 (Agent Runtime Environment)**，旨在通过模拟故事中的约束条件（资源限制、安全审计），探索 AI 辅助编程的极限。

## I. 概念映射表 (The Mapping)

我们将故事中的玄学概念“坍缩”为现实中的工程实体：

| 核心概念                       | 故事设定 (Fiction)                     | 现实工程实现 (Reality)                                                                                                                                                   |
| :----------------------------- | :------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Mental Sync™**               | 连接生物脑与数字链的神经桥接协议       | **CLI / Agent Framework**<br>一个自动化任务执行器，人类通过 TUI/WebUI 下达指令，而非神经信号。                                                                           |
| **PoPI**<br>(预测完整性证明)   | 基于自由能原理的意识连续性数学证明     | **CI/CD & User Satisfaction**<br>1. **代码可执行性**：Linter 通过，无语法错误。<br>2. **单元测试**：`pytest` 全绿。<br>3. **人类满意度**：操作员未回滚代码，未手动干预。 |
| **OSPU**<br>(衔尾蛇安全处理器) | 基于 FHE (全同态加密) 的物理硬件根信任 | **Orchestration Gateway (OG)**<br>基于 Docker/Podman 的容器隔离环境 + API 流量网关。没有魔法加密，只有权限管理。                                                         |
| **ΩNN**<br>(衔尾蛇神经网络)    | 产生主观体验 (Qualia) 的意识引擎       | **LLM API + Context Management**<br>调用 GPT-4/Claude 等外部模型。所谓的“意识”只是 Prompt 上下文的连贯性。                                                               |
| **CSC**<br>(认知智能合约)      | 神经信号转录的可编程行为链             | **Skills / Cron Jobs**<br>用 Markdown/YAML 定义的任务模板、自动化脚本和定时任务。                                                                                        |

## II. 架构详解：从神话到代码

### 1. 用户界面 (The Dashboard)

- **Fiction**: 视网膜投影的 HUD，直接叠加在视觉皮层，显示生命体征、Gas 余额和数字荒野的威胁。
- **Reality**: **TUI (Text User Interface) / WebUI**。
  - **功能**: 一个普通的管理后台。
    - **Kanban**: 任务看板，显示 To-Do/Doing/Done。
    - **System Status**: 显示 Token 消耗（钱）、API 延迟、Docker 容器状态。
    - **ChatBox**: 传统的对话框，用于给 Agent 发送文本指令。
  - **本质**: 它是可选的。MSC 可以在 Headless 模式下运行，Dashboard 只是为了让人类看着安心。

### 2. 核心编排 (The Gateway)

- **Fiction**: 绝对客观的逻辑仲裁者，在加密域内执行代码，防止数字实体被篡改。
- **Reality**: **Python/Rust 中间件**。
  - **Context Isolation**: 为每个 Task 启动一个独立的 Docker 容器，防止 `rm -rf /`。
  - **Traffic Control**: 限制 API 调用速率，防止 LLM 刷爆信用卡。
  - **Credential Management**: 拦截并注入 API Key，确保 Worker 进程（及 LLM）永远看不到真实的 Key。

### 3. 智能体 (Subagent & Reflect-Agent)

- **Fiction**: 独立的数字生命，拥有求生欲，会为了生存而优化自己的代码。
- **Reality**: **Stateless Worker Processes & Optimization Scripts**。
  - **Subagent**: 只是一个被生成的进程，跑完任务就销毁。它没有“求生欲”，只有 `max_retries` 配置。
  - **Reflect-Agent**: 这不是一个在冥想的 AI。它只是一个**定时脚本 (Cron Job)**。
    - **工作流**: 每天凌晨运行 -> 读取昨天的日志 -> 发送给 LLM -> 让 LLM 总结成 Markdown -> 存入 `knowledge_base/`。
    - **目的**: 减少 Token 消耗（省钱）和避免重复错误（提效）。

### 4. 上下文管理 (Context Hierarchy)

- **Fiction**: 推断空间 (Inference Space) 的几何结构，意识是沿测地线的运动。
- **Reality**: **Log Files & Vector Database**。
  - **Inference Trace**: 就是详细的 JSON 日志。
  - **State Transform Log**: Git Commit History。
  - **Task-Centric Summaries**: LLM 生成的文本摘要。
  - **机制**: 简单的 RAG (检索增强生成)。当执行新任务时，搜索以前类似的日志作为 Few-Shot Examples 塞进 Prompt。

## III. 核心机制：现实版 PoPI

在现实工程中，我们无法衡量“预测误差”或“自由能”。我们将 **PoPI (Proof of Predictive Integrity)** 重新定义为**工程质量指标**：

1. **Syntactic Validity (语法有效性)**:
   - Agent 生成的代码必须能通过 `ruff` (Python) 或 `cargo check` (Rust)。
   - _故事隐喻_: 类似于“思维的连贯性”。

2. **Functional Correctness (功能正确性)**:
   - 必须通过配套的单元测试 (`pytest` / `cargo test`)。
   - _故事隐喻_: 类似于“预测与感官输入的一致性”。

3. **Operator Satisfaction (操作员满意度)**:
   - 这是终极的 Ground Truth。如果人类操作员不得不介入（修改代码、终止进程），视为 PoPI 失败。
   - _故事隐喻_: 类似于“外部观察者（OSPU）的审计通过”。

**自举 (Bootstrapping) 的真相**:
所谓的“自举”，在现实中就是**自动化重构**。系统检测到某类任务经常导致 PoPI 失败（报错或被人工修改），Reflect-Agent 就会尝试修改对应的 Prompt 模板或 System Message，试图在下一次做得更好。这是一种**基于反馈的参数优化**，而非生物进化。

## IV. 总结

由于Tiny-ONN等组件并未就绪，目前的 Mental-Sync-CLI 是一个**披着科幻外衣的自动化工程工具**，顺便还能玩玩 **M**ental-**S**ync-**C**LI 的缩写梗。

- 我们使用 **Web://Reflect** 的术语，是因为它们提供了一套优雅的词汇来描述“自主优化的自举智能体”这一系统论问题。
- 但在代码实现层面，我们只相信 **Git**, **Docker**, **CI/CD** 和 **Unit Tests**。
