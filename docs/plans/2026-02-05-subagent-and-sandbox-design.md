# Action Plan: Sub-agent & Sandbox Implementation (Windows Focus)

> "Isolation is the first step towards sovereignty; logic is the final defense."

## 1. Sub-agent 混合模式实现 (Hybrid Mode)

### 1.1 逻辑隔离与身份绑定

- **ContextVar 绑定**: 在 `msc/core/og.py` 的 `Session` 循环中，使用 `contextvars` 确保每个 subagent 协程拥有独立的 `agent_id` 上下文。
- **Dispatcher 增强**: 修改 `ToolContext`，使其在初始化时自动从 `ContextVar` 获取 `agent_id`，防止 LLM 伪造。

### 1.2 进程派生 (Process Spawning)

- **CreateAgentTool**:
  - 不再仅仅返回一个 ID，而是实例化一个新的 `Session` 对象。
  - 初始版本：在主进程内以协程方式运行新 `Session`。
  - 进阶版本：通过 `multiprocessing` 或 `subprocess` 启动独立的 `msc-worker` 进程，通过 `Bridge` (JSON-RPC) 进行跨进程通信。

## 2. Windows 沙箱增强 (NFSS v2.0)

### 2.1 Restricted Token (受限令牌)

- **实现路径**: 使用 `pywin32` 调用 `advapi32.CreateRestrictedToken`。
- **策略**:
  - 移除 `BUILTIN\Administrators` 组。
  - 禁用所有不必要的 Privileges (如 `SeDebugPrivilege`)。
  - 添加 `RESTRICTED` SID。

### 2.2 Job Object (作业对象)

- **资源限制**:
  - 设置 `JOBOBJECT_EXTENDED_LIMIT_INFORMATION` 限制内存和 CPU。
  - 设置 `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` 确保主进程退出时子进程强制终止。
- **UI 隔离**: 设置 `JOB_OBJECT_BASIC_UI_RESTRICTIONS` 禁止子进程访问剪贴板或创建顶级窗口。

## 3. PFMS 路由与重试逻辑

### 3.1 错误感知重试

- **Oracle 升级**:
  - 捕获 `429` (Rate Limit) 并根据 `Retry-After` 延迟重试。
  - 捕获 `5xx` (Server Error) 立即切换至下一个物理实例。
- **Gas Limit 记录**:
  - 在 `MetadataProvider` 中增加 `gas_used` 字段，记录当前会话的总 Token 消耗。

## 4. 叙事元素集成

- **CLI 渲染**:
  - 将 `Token Usage` 替换为 `Gas Consumption`。

## 5. 验证计划 (TDD)

- `tests/core/test_security.py`: 验证 Windows 下受限令牌是否生效（尝试访问管理员目录）。
- `tests/core/test_og_session.py`: 验证多 subagent 并行运行时的 `agent_id` 隔离。
- `tests/oracle/test_pfms.py`: 模拟 500 错误验证自动切换逻辑。
