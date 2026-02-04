# subagent 规范与生命周期

> "subagents are the specialized workers of the MSC ecosystem, isolated by design and coordinated by intent."

## 1. 定义与核心原则

subagent 是 MSC 中的原子执行单元。每个 subagent 都是一个独立的 `Agent Core` 实例，运行在受限的沙箱环境中。

- **显式初始化**: 必须通过 `create_agent` 函数显式创建。
- **无状态继承**: subagent 不继承 Main Agent 的对话历史（Hot Memory），仅接收任务描述和必要的共享内存。
- **PFMS 绑定**: 创建时必须指定逻辑模型，由 PFMS 负责物理路由。

## 2. 初始化接口 (Create API)

```python
def create_agent(
    task_description: str,
    model_name: str,
    human_in_loop: bool = False,
    shared_memory: Optional[Dict[str, Any]] = None,
    sandbox_config: Optional[SandboxConfig] = None
) -> str:
    """
    创建一个新的 subagent 实例。
    
    Args:
        task_description: 任务的具体描述和指令。
        model_name: 逻辑模型名称（需在 PFMS 中定义）。
        human_in_loop: 是否强制开启人类审批模式。
        shared_memory: 传递给 subagent 的 Anamnesis 共享内存片段。
        sandbox_config: 细粒度的沙箱权限配置（文件读写、网络等）。
        
    Returns:
        agent_id: 唯一标识符，用于后续状态查询和审批路由。
    """
```

## 3. 认知与内存模型

### 3.1 任务上下文 (Task Context)

subagent 的 `System Prompt` 由以下部分动态组合：

1. **Base Identity**: 通用的 subagent 行为准则。
2. **Task Instruction**: `task_description` 传入的具体指令。
3. **Shared Memory**: `Anamnesis` 提供的只读或读写共享数据块。

### 3.2 独立性

subagent 拥有独立的工具调用栈和思考循环。其产生的 `Inference Trace` 会被记录，但不会直接污染 Main Agent 的上下文，除非任务完成后的结果返回。

## 4. 生命周期管理

### 4.1 状态监控

Interface 层必须提供任务管理器视图，支持：

- **LIST**: 列出所有活跃的 `agent_id` 及其当前状态（Running, Waiting for Approval, Finished, Failed）。
- **SWITCH**: 切换当前 UI 焦点到特定 subagent，查看其详细的思考日志。
- **KILL**: 强制终止特定 subagent 进程。

### 4.2 审批路由

- 所有 subagent 的审批请求必须携带 `agent_id`。
- OG 负责将请求路由至 Bridge，Interface 根据 `agent_id` 渲染对应的上下文。
- **拒绝策略**: 拒绝审批仅导致该 subagent 的当前请求失败，不影响其进程存续（除非 subagent 逻辑决定在审批失败时退出）。

## 5. 错误处理与清理

- **孤儿进程保护**: 若 Main Agent 崩溃，OG 必须负责清理所有派生的 subagent 进程。
- **结果回传**: subagent 完成任务后，通过内部 IPC（函数返回）将结果同步给 Main Agent。
