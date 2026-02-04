# create_subagent 函数正式定义 (MSC v3.0)

> "Identity is fluid, but the protocol is immutable."

## 1. 函数签名

```python
async def create_subagent(
    task_description: str,
    model_name: str = "auto",
    require_caps: Optional[List[str]] = None,
    require_thinking: bool = False,
    shared_memory: bool = False,
    sandbox_config: Optional[Dict[str, Any]] = None
) -> str:
    """
    创建一个新的 Sub-agent 实例并返回其唯一标识符 agent_id。
    
    Args:
        task_description: 子任务的具体指令。
        model_name: 逻辑模型名称。必须先调用 model-select-advice 获取建议。
        require_caps: 强制筛选的能力标签（如 GreenTEA, Vision, Voice）。
        require_thinking: 是否强制要求 CoT 推理能力。
        shared_memory: 是否允许子代理访问父代理的 Anamnesis 记忆片段。
        sandbox_config: 细粒度的沙箱权限配置（文件白名单等）。
        
    Returns:
        agent_id: 用于后续通信的唯一 ID。
    """
```

## 2. 核心行为准则

1. **HIL 强制性**: `create_agent` 的调用是一个 Human-In-Loop 事件。
2. **前置依赖**: 在调用此函数前，Agent **必须** 已经通过 `model-select-advice` 技能向用户展示了选购建议并获得确认。
3. **异步解耦**: 函数立即返回 `agent_id`，子代理在独立的沙箱进程中启动。
4. **通信协议**:
   - 使用 `ask_agent(agent_id, priority, message)` 进行后续交互。
   - `priority="standard"`: 消息进入子代理队列，作为下一条 User Message 处理。
   - `priority="high"`: 立即打断子代理当前任务（仅限父代理对子代理使用）。
