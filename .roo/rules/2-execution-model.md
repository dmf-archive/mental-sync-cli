# MSC Execution Model: Hybrid Coroutine-Process Architecture

> "Context flows through Oracle; danger is sandboxed in process."

## 1. 核心原则

MSC v3.0 采用 **模型 B: 上下文协程 + 工具调用隔离**。

- **模型推理 (LLM 调用)**: 异步协程，通过共享的 `Oracle` 实例进行负载均衡。
- **工具执行**: 危险操作（文件写入、命令行执行）在 **子进程** 中执行，受 **NFSS (Native Filesystem Sandbox)** 约束。

## 2. 架构分层

```
┌─────────────────────────────────────────┐
│         Main Process (Python)            │
│  ┌─────────────────────────────────┐    │
│  │      Shared Oracle Instance      │    │
│  │  (Async, Load-Balanced Routing)  │    │
│  └─────────────────────────────────┘    │
│                   │                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐    │
│  │ Agent 1 │ │ Agent 2 │ │ Agent 3 │    │
│  │ (async) │ │ (async) │ │ (async) │    │
│  └────┬────┘ └────┬────┘ └────┬────┘    │
│       └───────────┴───────────┘          │
│              Tool Dispatcher             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐    │
│  │Process  │ │Process  │ │Process  │    │
│  │write_f  │ │shell_e  │ │fetch_u  │    │
│  │(NFSS)   │ │(NFSS)   │ │(NFSS)   │    │
│  └─────────┘ └─────────┘ └─────────┘    │
└─────────────────────────────────────────┘
```

## 3. 组件职责

### 3.1 Oracle (共享实例)

- **唯一职责**: 接受组装好的上下文，生成文本补全 (Token/Message)。
- **并发模型**: 纯异步协程，`aiohttp` 驱动。
- **生命周期**: 整个 MSC Instance 共享同一个 `Oracle` 对象。

### 3.2 Context Manager (协程)

- **职责**: 组装不同 Sub-agent 的上下文，管理对话历史 (Log)。
- **并发模型**: 每个 Sub-agent 一个协程任务，共享事件循环。

### 3.3 Tool Executor (子进程)

- **触发时机**: 仅当工具调用发生时。
- **隔离机制**: **NFSS (Native Filesystem Sandbox) v2.0**。
  - **核心实现**: 强制使用 `create_subprocess_exec` 替代 `shell=True`，从根本上杜绝 Shell 注入。
  - **Linux**: 采用 `bwrap` (Bubblewrap) 封装 `Landlock` 与 `Namespaces`。实现 `unshare-all` 隔离网络、IPC、UTS，并利用 `--ro-bind / /` 实现默认只读，通过 `--bind` 显式授权。
  - **macOS**: 采用 `sandbox-exec` (Seatbelt)。通过生成的 `.sb` 配置文件实现 `(deny default)` 策略，精细化控制 `file-read*` 与 `file-write*` 权限。
  - **Windows**: 采用 `Restricted Token` + `Job Object`。移除管理员权限并添加 `RESTRICTED` SID，限制 UI 句柄与资源消耗。
- **ACL 控制**: 采用“物理隔离优先”原则。ACL 表在启动前被转换为平台特定的沙箱参数，由 OS 内核强制执行，免疫 TOCTTOU 与符号链接绕过。

## 4. TEA (Trust-Execution-Agent) 澄清

TEA 的本质是 **Provider 路由策略**，而非额外的安全层。

- **TEA 的 Provider**: 仅路由给具备 `green-tea` 标签的 Provider（如本地 Ollama）。
- **安全边界**: TLS 加密传输，但数据在 Provider 端是明文。
- **结论**: TEA 不需要额外的进程隔离，因为它不执行本地代码。

## 5. 关键不变量 (Invariants)

1. **Oracle 单例**: 整个 Instance 只有一个 `Oracle` 实例。
2. **工具即进程**: 任何可能修改系统状态的操作必须在子进程中执行。
3. **ACL 动态化**: 沙箱权限在工具调用时通过 `sandbox_config` 动态注入，而非静态配置。
4. **协程状态**: Sub-agent 的协程维护持久状态，状态由协程内调用的 `Anamnesis` 相关函数管理。

## 6. 测试策略

- **单元测试**: Mock Oracle，验证工具 Schema 和参数校验。
- **集成测试**: 验证工具子进程的生命周期管理（启动、执行、清理）。
- **安全测试**: 验证 NFSS 拦截能力（尝试越界访问）。
