# MSC Architecture v3.0 (TDD Redesign)

> "Security by isolation, efficiency by design."

## 核心架构原则

1. `分层沙箱`: Docker (可选外层) → Native FS Sandbox (原生隔离) → Sub-agent 实例
2. `Agent Core 复用`: 所有 Sub-agent 都是完整的 Agent Core Instance
3. `特殊 Sub-agent`: TEA, Organizer 拥有独立的 Agent Core 定义
4. `Bridge 解耦`: 连接 Interface 与 Gateway 的轻量级消息总线

## 系统架构图

```mermaid
graph TB
    subgraph "Host OS"
        direction TB

        subgraph "Docker Container (Optional)"
            direction TB

            subgraph "Interface Layer"
                CLI["CLI Interface<br/>(Typer + Rich)"]
                WEB["Web UI<br/>(Future)"]
            end

            subgraph "Bridge Layer"
                BRIDGE["Bridge Bus<br/>(Message Router)"]
            end

            subgraph "Orchestration Gateway (OG)"
                OG_CORE["OG Core<br/>(Session Manager)"]
                PS["Provider-Selector<br/>(Model Routing)"]
                PERM["Permission Manager<br/>(Approval Flow)"]
            end

            subgraph "Agent Core"
                MAIN["Main Agent<br/>(Cognitive Loop)"]
                ANAM["Anamnesis<br/>(Context Manager)"]
                SKILLS["Skills Registry<br/>(MCP + .agent/skills)"]
            end

            subgraph "Sandbox Layer (NFSandbox)"
                direction TB

                subgraph "Standard Sub-agents"
                    SA1["Sub-agent 1<br/>(Agent Core Instance)"]
                    SA2["Sub-agent 2<br/>(Agent Core Instance)"]
                    SA3["Sub-agent N<br/>(Agent Core Instance)"]
                end

                subgraph "Special Sub-agents"
                    TEA["TEA<br/>(Trust-Execution-Agent)<br/>[Custom Agent Core]"]
                    ORG["Organizer<br/>(Global Memory & Trace)<br/>[Custom Agent Core]"]
                end

                subgraph "Tool Executors"
                    MCP_EXEC["MCP Tool Servers"]
                end
            end
        end
    end

    %% Connections - Interface to Bridge
    CLI --> BRIDGE
    WEB --> BRIDGE

    %% Connections - Bridge to OG
    BRIDGE --> OG_CORE

    %% Connections - OG Internal
    OG_CORE --> PS
    OG_CORE --> PERM

    %% Connections - OG to Main Agent
    PS --> MAIN
    PERM -.->|Approval Request| MAIN

    %% Connections - Main Agent Internal
    MAIN --> ANAM
    MAIN --> SKILLS

    %% Connections - Main Agent to Sandbox
    MAIN -->|Spawn| SA1
    MAIN -->|Spawn| SA2
    MAIN -->|Spawn| SA3

    %% Connections - Special Sub-agents
    PS -.->|Secure Provider| TEA
    OG_CORE -.->|Schedule| ORG

    %% Connections - Tools
    SA1 --> MCP_EXEC
    SA2 --> MCP_EXEC
    TEA -->|Restricted MCP| MCP_EXEC

    %% External
    LLM["LLM Providers<br/>(OpenAI/Anthropic/etc)"] -.-> MAIN
    LLM -.-> SA1
    LLM -.-> SA2
    LLM -.->|Secure Provider| TEA
```

## 组件定义

### 1. Interface Layer (交互层)

- `CLI`: 基于 Typer + Rich 的终端界面
- `Web UI`: 未来扩展的 Web 界面 (通过 Bridge 接入)

### 2. Bridge Layer (桥接层)

- `前身`: Wire Protocol (kimi-cli 概念)
- `职责`: 轻量级 JSON 消息总线，解耦 Interface 与 Gateway
- `必要性`: 支持多前端共享同一后端逻辑
- `设计目标`: 极简实现，避免 kimi-cli Wire 的复杂度

### 3. Orchestration Gateway (OG) (编排网关)

- `OG Core`: 会话生命周期管理，协调各组件
- `Provider-Selector`: 根据任务复杂度、成本、安全需求路由到不同模型
- `Permission Manager`: 统一审批中心。支持 `agent_id` 路由，管理 `HIL` (Human-In-Loop) 状态。

### 4. Agent Core (认知核心)

- `Main Agent`: 主认知循环（感知-决策-执行）
- `Anamnesis`: 上下文管理器 (ContextManager)，管理 Hot/Cold 记忆分离
  - _注意_: 虽逻辑上类似受限 sub-agent，但不作为独立 Agent 实例运行
- `Skills`: MCP 工具 + `.agent/skills` 声明式技能注册表

### 5. Sandbox Layer (NFSandbox) (沙箱层)

- `Native Filesystem Sandbox`: 平台原生隔离机制
  - Linux: Landlock + seccomp
  - Windows: Windows Sandbox / Restricted Token
  - macOS: Seatbelt
- `Docker`: 可选的最外层容器，开发时可忽略

### 6. Sub-agents (子智能体)

#### 6.1 Standard Sub-agents (标准子代理)

- `本质`: 每个都是完整的 Agent Core Instance
- `生命周期`: 由 Main Agent 按需 Spawn
- `用途`: 执行具体任务、工具调用、并行处理

#### 6.2 Special Sub-agents (特殊子代理)

| Sub-agent   | 特殊之处              | Agent Core | 职责                           |
| ----------- | --------------------- | ---------- | ------------------------------ |
| `TEA`       | Trust-Execution-Agent | 能力标签   | 凭证隔离、敏感操作、支付处理   |
| `Organizer` | 全局记忆访问          | 自定义     | 制作 Cold Memory Card、管理 Main Agent 的 Hot Memory、知识蒸馏 |

## 7. 认知上下文布局 (Context Layout)

为了对抗注意力稀释并优化推理效率，MSC 采用标准化的 System Prompt 布局。详细的布局规范、记忆分层逻辑及 `Lite RAG` 机制请参阅 [`.roo/rules/anamnesis-and-context-manager.md`](.roo/rules/anamnesis-and-context-manager.md)。

## 数据流与审批协议

### 1. 审批流 (Approval Flow)

MSC 采用“异步消息，同步阻塞”的混合审批模型：

- `Main Agent & TEA`: 强制 `HIL` (Human-In-Loop)。审批请求通过 Bridge 异步发送至 Interface，但 Agent 认知循环在收到响应前保持阻塞。
- `Sub-agents`: 默认同步审批。审批请求在 Python 进程内通过函数调用传递，仅阻塞当前 Sub-agent 实例，不影响 Main Agent 或其他并行 Sub-agents。
- `路由元数据`: 所有审批请求必须携带 `agent_id`。Interface 根据此 ID 渲染对应的上下文，确保用户知晓审批来源。
- `拒绝策略`: 拒绝审批仅取消当前请求。已运行的 Sub-agents 及其权限不受影响，维持系统运行的连续性。

### 2. 交互序列图

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Bridge
    participant OG
    participant Main
    participant SubAgent

    User->>CLI: 输入指令
    CLI->>Bridge: 异步消息 (JSON-RPC)
    Bridge->>OG: 路由至 Session
    OG->>Main: 启动认知循环

    Note over Main, SubAgent: 并行执行阶段

    rect rgba(0, 0, 0, 1)
        Note right of SubAgent: Sub-agent 同步审批
        SubAgent->>Main: 请求权限 (Python Call)
        Main->>OG: 转发审批 (agent_id=SA_1)
        OG->>Bridge: 异步推送请求
        Bridge->>CLI: 弹出 HIL 界面
        User-->>CLI: 点击 [允许]
        CLI-->>Main: 返回结果 (via Bridge/OG)
        Main-->>SubAgent: 授权通过
    end

    Main->>OG: 任务完成
    OG->>Bridge: 最终响应
    Bridge->>CLI: 渲染结果
```

## TDD 测试边界

| 组件              | 测试策略            | 关键测试点             |
| ----------------- | ------------------- | ---------------------- |
| Bridge            | 消息序列化/反序列化 | 跨进程通信、消息路由   |
| OG                | 会话状态机          | 生命周期管理、错误恢复 |
| Provider-Selector | 模型路由决策        | 成本估算、安全分级     |
| Main Agent        | 认知循环逻辑        | 工具调用链、上下文传递 |
| Anamnesis         | 上下文压缩          | Token 截断、记忆分层   |
| Sandbox           | 路径隔离            | 越界访问拦截、权限降级 |
| Sub-agent         | Agent Core 实例化   | 启动速度、资源清理     |
| TEA               | 凭证注入            | 密钥不可见性、审计日志 |
| Organizer         | 全局记忆            | Trace 生成、知识提取   |

## 沙箱层级详解

```mermaid
graph LR
    subgraph "沙箱层级 (由内到外)"
        direction TB

        L1["L1: Sub-agent Process<br/>(Agent Core Instance)"]
        L2["L2: Native FS Sandbox<br/>(Landlock/Seatbelt/RestrictedToken)"]
        L3["L3: Docker Container<br/>(Optional Outer Layer)"]
    end

    L1 --> L2 --> L3
```

- `L1 (Process)`: 每个 Sub-agent 是独立的 Python 进程，拥有完整的 Agent Core
- `L2 (Native)`: 平台原生机制限制文件系统访问
- `L3 (Docker)`: 可选的额外隔离层，开发时可跳过直接使用 L2
