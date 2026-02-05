# 架构决策：显式任务完成工具 (complete_task)

## 1. 背景与动机

在 MSC 的子代理生命周期管理中，目前依赖模型输出 `FINISH` 关键字来终止 `run_loop`。这种方式存在以下缺陷：

- **状态模糊**：`FINISH` 仅代表模型认为自己说完了，不代表任务成功或失败。
- **通信脱节**：子代理可能在没有向父代理汇报结果的情况下直接 `FINISH`。
- **测试困难**：难以在测试中精确断言任务的最终交付状态。

为了实现强状态控制，我们引入显式工具 `complete_task`。

## 2. 方案对比

| 维度 | 方案 A：独立工具 `complete_task` | 方案 B：`ask_agent` 扩展参数 |
| :--- | :--- | :--- |
| **语义清晰度** | 极高。专门用于终止生命周期并提交结果。 | 一般。容易与普通对话混淆。 |
| **控制流影响** | 强。调用后 `SessionStatus` 立即变为 `COMPLETED`。 | 弱。需要解析消息内容来决定是否终止。 |
| **代码解耦** | 好。工具逻辑独立，不污染通信接口。 | 差。通信接口承载了过多的控制逻辑。 |
| **测试断言** | 简单。直接检查 `SessionStatus` 和 `task_result` 消息。 | 复杂。需要扫描历史记录并解析 JSON 消息。 |

**决策：选择方案 A (独立工具 `complete_task`)。**

## 3. 变更清单

### 3.1 规范修订

- [ ] **`.roo/rules/minimal_tool.md`**:
  - 添加 `complete_task(status(str);summary(str);data(dict))` 到最小工具集。
  - 明确 `status` 可选值为 `success`, `failed`。
- [ ] **`.roo/rules/subagent.md`**:
  - 规定子代理必须使用 `complete_task` 结束任务，而非仅靠 `FINISH`。

### 3.2 代码实现

- [ ] **`msc/core/tools/agent_ops.py`**:
  - 实现 `CompleteTaskTool` 类。
  - 该工具执行时，应自动向 `parent_agent_id` 发送一条类型为 `task_result` 的结构化消息。
- [ ] **`msc/core/og.py`**:
  - 在 `Session.run_loop` 中，捕获 `complete_task` 的调用并强制设置 `self.status = SessionStatus.COMPLETED`。
  - 确保 `complete_task` 的结果回传逻辑在 `run_loop` 中被正确处理。

### 3.3 测试验证

- [ ] **`tests/core/test_subagent_blacklist_e2e.py`**:
  - 编写 E2E 测试，模拟子代理访问黑名单目录失败后，调用 `complete_task` 汇报 `failed` 状态。

## 4. 预期效果

子代理将拥有明确的“交付”动作。父代理（Main Agent）在收到 `task_result` 消息后，可以根据 `status` 字段决定是继续重试还是宣布整体任务完成。
