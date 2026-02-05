# Action Plan: Sub-agent & Sandbox Implementation (Windows Focus)

> "Isolation is the first step towards sovereignty; logic is the final defense."

## 1. Sub-agent 架构：协程上下文 + 进程沙箱工具

### 1.1 逻辑实体与协程绑定

- **Agent as Coroutine**: 每个 Agent 实例（包括 Main Agent 和 subagents）在逻辑上表现为一个独立的协程 ID。
- **Context 隔离**: 使用 `contextvars` 维护 `agent_id` 和 `ACL`。`ask_agent` 的本质是向目标协程的 `history` 中插入一条 `user` 消息，实现注意力的聚焦协同。
- **无感 IPC**: 代理间的通信通过共享的 `Orchestration Gateway (OG)` 消息总线完成，避免复杂的双向异步网络通信，防止信息流弥散。

### 1.2 动态沙箱派生 (Just-in-Time Sandboxing)

- **工具即进程**: 只有在调用涉及外部环境的工具（如 `execute`, `write_file`）时，才根据当前 Agent 的 `ACL` 转换为 `NFSS` 隔离策略。
- **原子化执行**: 每次工具调用派生一个受限的沙箱进程（Windows 下使用 `Restricted Token` + `Job Object`），执行完毕后立即销毁，确保环境的“逻辑根信任”。

## 2. Session 持久化：多线程独立记录 (Threaded Session)

### 2.1 存储结构 (Filesystem Layout)

Session 采用“一会话一目录”的结构，将主代理与子代理的对话线程物理隔离：

```text
storage/sessions/{timestamp}-{salt}/
├── main-agent.json      # 主代理对话记录
├── agent-sub-123.json   # 子代理 A 记录
└── agent-sub-456.json   # 子代理 B 记录
```

### 2.2 文件格式 (JSON Schema)

每个 `.json` 文件包含独立的元数据头和对话历史：

- **Header**: 包含 `agent_id`, `model_name`, `gas_used`, `status`, `start_time`。
- **History**: 标准的 `role/content` 消息数组。
- **ACL 隔离**: ACL 表不随 Session 记录，由全局/项目配置动态注入。

## 3. Gas 计费器 (Gas Metering)

### 3.1 计费逻辑 (Centralized Metering)

- **Provider 响应拦截**: `Oracle` 在返回 LLM 响应时，必须解析并返回 `usage` 数据（Input/Output/Thinking tokens）。
- **Gas 转换**: `OG` 维护全局 `GasTracker`，根据 `config.yaml` 中的模型单价将 Token 转换为 `Gas` 消耗。
- **持久化**: 实时更新 `$HOME/.msc/gas-vault.json`，支持会话级和全局级的 `Gas Limit` 拦截。

## 4. Windows 沙箱增强 (NFSS v2.0)

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
