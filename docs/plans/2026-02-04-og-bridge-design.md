# MSC v3.0: 编排网关 (OG) 与 桥接层 (Bridge Layer) 设计方案

> "桥接层连接意图与行动；网关确保行动符合逻辑。"

## 1. 编排网关 (Orchestration Gateway, OG) 架构

OG 是 MSC 的中枢神经系统，负责管理智能体的生命周期，并在认知核心与外部世界之间进行调解。

### 1.1 会话管理器 (Session Manager)

- **实体**: `Session`
- **状态**: `IDLE` (空闲), `RUNNING` (运行中), `AWAITING_APPROVAL` (等待审批), `COMPLETED` (已完成), `FAILED` (失败)
- **核心组件**:
  - `Oracle`: 共享的单例，负责模型路由。
  - `MainAgent`: 主认知循环。
  - `AgentRegistry`: `Dict[str, AgentInstance]`，跟踪所有活跃的子代理。

### 1.2 权限管理器 (Permission Manager / HIL)

- **机制**: 通过 `asyncio.Event` 实现异步阻塞。
- **流程**:
    1. 工具调用 `og.request_permission(agent_id, action, params)`。
    2. OG 生成 `request_id` 并向桥接层推送 `msc/approval_required` 消息。
    3. 工具执行协程在 `event.wait()` 处挂起。
    4. 桥接层接收到 `msc/approve` 或 `msc/deny`。
    5. OG 设置事件状态并向工具返回结果。

### 1.3 Provider 选择器 (Provider-Selector)

- 实现 `PFMS.md` 中定义的逻辑。
- 根据“逻辑模型”名称和任务需求（视觉、思考、成本）动态选择最佳的“物理实例”。

## 2. 桥接层协议 (Bridge Layer Protocol - JSON-RPC 2.0 风格)

桥接层使用异步消息总线将 CLI/UI 与 OG 核心解耦。

### 2.1 代理 -> 界面 (下行消息)

| 方法 | 参数 | 描述 |
| :--- | :--- | :--- |
| `msc/log` | `agent_id`, `content`, `type` | 实时思考日志或输出流。 |
| `msc/approval_required` | `request_id`, `agent_id`, `action`, `data` | 人类干预/审批请求。 |
| `msc/session_update` | `status`, `active_agents` | 全局会话状态变更。 |

### 2.2 界面 -> 代理 (上行消息)

| 方法 | 参数 | 描述 |
| :--- | :--- | :--- |
| `msc/input` | `text` | 用户指令或反馈。 |
| `msc/approve` | `request_id`, `approved`, `reason` | 对权限请求的响应。 |
| `msc/abort` | `agent_id` | 强制终止特定代理或整个会话。 |

## 3. CLI 界面设计 (Typer + Rich)

### 3.1 布局设计

- **页眉 (Header)**: 会话状态、模型信息、成本统计。
- **主面板 (Main Panel)**: 使用 `Rich.Live` 展示实时日志流。
- **侧边栏/状态栏**: 活跃子代理列表及其当前状态。
- **输入区**: 用于输入指令和 HIL 决策的交互式提示符。

### 3.2 交互逻辑

- 使用 `Prompt.ask` 处理 HIL 决策。
- 支持“全局热键”（例如：`Ctrl+C` 按一次中断当前代理，按两次终止整个会话）。

## 4. 实施路线图

1. **阶段 1**: 定义 `msc.core.og` 和 `msc.core.bridge` 基类。
2. **阶段 2**: 使用 Mock 桥接层实现 `PermissionManager`。
3. **阶段 3**: 在 `main.py` 中构建基于 `Typer` 的 CLI 入口。
4. **阶段 4**: 实现 `Session.run_loop` 与 `ToolParser`。
5. **阶段 5**: 将 `Anamnesis` 和 `Oracle` 集成到 `Session` 流程中。
