# MSC 测试体系重构指南：从 V2 碎片化验证到 V3 链路驱动

> "测试不是为了证明代码能跑，而是为了定义协议的边界。"

本文档旨在梳理旧测试体系的理论目的，并指导如何将其核心逻辑无损迁移至 V3 场景驱动的测试套件中。

---

## 1. 旧测试体系：理论目的与细节拆解

### 1.1 `test_security.py` & `test_minimal_tools.py`

- **理论目的**：验证 **NFSS (Native Filesystem Sandbox)** 的物理隔离能力。
- **核心细节**：
  - `icacls` 模拟：验证 Windows 下文件权限的显式拒绝。
  - `whoami /groups`：验证 `Restricted Token` 是否成功将 Administrators 组标记为 `deny only`。
  - `curl` 拦截：验证防火墙规则是否生效。
- **V3 承载**：`test_sandbox_tools.py`。
- **迁移要求**：必须保留对 `sandbox_launcher.py` 启动参数的精确校验，并增加对环境变量污染（`HTTP_PROXY=127.0.0.1:0`）的验证。

### 1.2 `test_context.py` & `test_metadata.py` & `test_rag.py`

- **理论目的**：验证 **Anamnesis (认知上下文引擎)** 的组装精度。
- **核心细节**：
  - 占位符替换：确保 `{{TASK_INSTRUCTION}}` 等标签被正确替换。
  - 启发式关键词：验证 `LiteRAG` 从对话中提取 `CamelCase` 或 `quoted strings` 的准确性。
  - 实时元数据：验证 `gas_used` 的累加逻辑。
- **V3 承载**：`test_context_engine.py`。
- **迁移要求**：无损转入 `normalize_history` 的逻辑验证，特别是对 `Message from agent-X` 这种跨代理 JSON 负载的 Markdown 渲染。

### 1.3 `test_session_persistence.py` & `test_og_session.py`

- **理论目的**：验证 **OG (Orchestration Gateway)** 的状态一致性与持久化。
- **核心细节**：
  - `ThreadedSessionRecord`：验证 Pydantic 模型在包含复杂 `ToolCall` 历史时的序列化。
  - `SessionStatus` 状态机：验证从 `IDLE` -> `RUNNING` -> `AWAITING_APPROVAL` 的转换。
- **V3 承载**：`test_session_lifecycle.py`。
- **迁移要求**：模拟断电重启场景，验证 Session 恢复后 `agent_registry` 的重新挂载。

### 1.4 `test_subagent_e2e.py` & `test_subagent_flow.py`

- **理论目的**：验证 **子代理生命周期与 IPC 协议**。
- **核心细节**：
  - `create_agent` ACL 继承：验证子代理的 `allowed_paths` 必须是父代理的子集。
  - `ask_agent` 路由：验证消息是否准确投递到目标 Session 的 history。
  - `complete_task` 级联：验证子代理结束如何唤醒父代理。
- **V3 承载**：`test_subagent_orchestration.py`。
- **迁移要求**：**严禁手动唤醒**。必须通过真实 LLM 调用 `complete_task` 触发 `task_result` 消息，验证父代理的自动感知。

---

## 2. V3 新测试套件的编写策略（拒绝狗屎逻辑）

### A. 真实 API 驱动 (No More Blind Mocking)

- 统一使用 `BASE_URL = "http://localhost:8317"`。
- 利用 Relay 支持多协议的特性，在同一个测试中混合使用 `OpenAIAdapter` 和 `AnthropicAdapter`，验证 `Oracle` 的跨协议兼容性。

### B. 协议闭环验证 (Protocol Closure)

- **不变量检查**：在每个 `run_loop` 步长后，断言 `SessionStatus`。
- **Gas 审计**：验证真实 API 返回的 `usage` 字段是否正确转换为 `gas_used`。

### C. 仿真环境隔离 (Mock Workspace)

- 每个测试使用独立的 `tmp_path`。
- 预置 `CLAUDE.md` 或 `.msc/rules/*.md`，验证 `RulesDiscoverer` 的自动注入。

---

## 3. 接下来我要怎么写（以 `test_subagent_orchestration` 为例）

1. **初始化**：配置三个 Provider（OpenAI, Anthropic, Gemini），其中 Gemini 绑定 `green-tea` 标签。
2. **指令下达**：给 Main Agent 下达一个需要“安全环境”的任务（触发 `green-tea` 路由）。
3. **子代理派生**：
    - 拦截 `create_agent` 调用，断言其 `sandbox_config` 中的 `allowed_paths` 权限缩减。
    - 启动子代理 Session。
4. **IPC 交互**：
    - 子代理执行任务，调用 `ask_agent` 发送进度。
    - **关键点**：验证 Main Agent 的 `ContextFactory` 是否将该 JSON 消息渲染成了 Markdown 引用。
5. **自动终结**：
    - 子代理调用 `complete_task`。
    - 验证 `OG` 自动将 `task_result` 注入 Main Agent。
    - 验证 Main Agent 感知到结果后，自主调用 `complete_task` 结束。
6. **最终断言**：检查 `test_storage` 下生成的两个 `.json` 持久化文件，确保历史记录完整。

---

**检讨总结**：我之前写的测试只是在“跑流程”，而真正的测试应该是在“考协议”。我将按此标准重写所有套件。
