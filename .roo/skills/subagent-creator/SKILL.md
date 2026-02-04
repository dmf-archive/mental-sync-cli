---
name: subagent-creator
description: "Proactively invoke this skill when needing to spawn a new subagent to handle specialized tasks, ensuring model selection advice is followed."
---

# Skill: subagent-creator

此技能指导智能体如何合规、安全地创建子代理（subagent）。创建子代理是 MSC v3.0 中的高权限 HIL 事件。

## 1. 触发流程 (RED Phase)

在调用 `create_agent` 工具之前，你**必须**完成以下步骤：

1. **加载建议**: 调用 `model-select-advice` 技能。
2. **展示对比**: 向用户展示 OpenRouter 实时价格与能力对比表。
3. **确认选购**: 明确询问用户：“我建议使用 [Model Name] 来处理此子任务，是否确认并创建子代理？”
4. **定义边界**: 明确子代理的 `sandbox_config`（允许访问的路径）。

## 2. 核心工具参考

- **API 定义**: [`references/api_spec.md`](references/api_spec.md)
- **通信工具**: `ask_agent(agent_id, priority, message)`

## 3. 常见借口与现实 (Rationalization Table)

| 常见借口 (Rationalization) | 现实 (Reality) |
| :--- | :--- |
| “任务很简单，我直接用默认模型创建就行。” | **违规**。必须强制调用 `model-select-advice` 以确保成本最优和能力匹配。 |
| “子代理需要访问整个项目目录。” | **危险**。必须遵循最小权限原则，在 `sandbox_config` 中仅列出必要的路径。 |
| “我可以直接在当前对话处理，不需要子代理。” | **低效**。对于需要独立思考空间、并行处理或异构模型（如 GreenTEA）的任务，子代理是唯一正确的选择。 |

## 4. 红灯信号 (Red Flags)

- [ ] **越权创建**: 在未获得用户对具体模型和价格的明确确认前调用 `create_agent`。
- [ ] **全量继承**: 将 `shared_memory` 设为 `True` 却未解释原因（默认应为 `False` 以保持隔离）。
- [ ] **静默失败**: 创建后未向用户返回 `agent_id`。
- [ ] **通信混乱**: 混淆了 `standard` 和 `high` 优先级的适用场景。

## 5. 现场演示 (Demo)

```python
# 1. 智能体首先调用 model-select-advice
# 2. 智能体向用户汇报：
# "根据实时数据，DeepSeek-V3 价格最低且支持代码审计。我建议创建子代理处理 src/ 目录的重构。"
# 3. 用户确认后，智能体执行：
create_agent(
    task_description="Refactor all files in src/ to follow REQ-101",
    model_name="deepseek-chat",
    require_caps=["vision"], # 示例
    sandbox_config={"allowed_read_paths": ["./src"], "allowed_write_paths": ["./src"]}
)
```
