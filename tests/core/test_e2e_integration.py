import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

import pytest

from msc.core.og import OrchestrationGateway, Session, SessionStatus
from msc.core.tools.base import ToolContext
from msc.core.tools.system_ops import ExecuteTool
from msc.oracle import Oracle, create_adapter

# 本地转发器配置 (来自 tests/oracle/test_integration.py)
BASE_URL = "http://localhost:8317"
API_KEY = "123456"
MODEL_ID = "gemini-2.5-flash-lite"

@pytest.mark.asyncio
async def test_e2e_cognitive_tool_hil_loop():
    """
    End-to-End 耦合测试：
    1. 组装 Anamnesis 上下文。
    2. 通过 Oracle 调用真实本地转发器。
    3. 模拟模型返回工具调用 (ExecuteTool)。
    4. 触发 OG 的 HIL 审批流。
    5. 验证工具在沙箱中执行并返回结果。
    """
    
    # --- 1. 环境准备 ---
    mock_bridge = AsyncMock()
    og = OrchestrationGateway(bridge=mock_bridge)
    
    # 创建真实适配器
    adapter = create_adapter(
        "openai", 
        name="local-proxy", 
        model=MODEL_ID, 
        api_key=API_KEY, 
        base_url=f"{BASE_URL}/v1"
    )
    oracle = Oracle(providers=[adapter])
    
    # --- 2. Session 初始化 ---
    session = Session(
        session_id="e2e-test-session",
        oracle=oracle,
        gateway=og,
        workspace_root=os.getcwd()
    )
    await session.start()
    
    # --- 3. 模拟工具调用请求 (由模型逻辑触发) ---
    # 在真实场景中，这是由 MainAgent 接收模型输出并解析得到的
    # 这里我们直接测试工具与 OG 的耦合
    
    tool_context = ToolContext(
        agent_id="main-agent",
        workspace_root=session.workspace_root,
        oracle=oracle,
        gateway=og,
        allowed_paths=[session.workspace_root]
    )
    execute_tool = ExecuteTool(tool_context)
    
    # 构造一个需要审批的场景
    command = "cmd.exe /c echo E2E_SUCCESS" if os.name == "nt" else "echo 'E2E_SUCCESS'"

    # 启动工具执行任务，它现在会自动触发 og.request_permission
    tool_task = asyncio.create_task(execute_tool.execute(command=command))
    
    # --- 4. 验证 HIL 触发 ---
    await asyncio.sleep(0.2) # 等待消息发送
    mock_bridge.send_message.assert_called()
    
    # 检查发送的消息格式是否符合 Bridge 协议
    last_call = mock_bridge.send_message.call_args[0][0]
    assert last_call["method"] == "msc/approval_required"
    assert last_call["params"]["action"] == "execute"
    
    # --- 5. 模拟用户批准 ---
    await og.handle_bridge_message({
        "method": "msc/approve",
        "params": {"request_id": "any", "approved": True}
    })
    
    # --- 6. 验证最终结果 ---
    result = await tool_task
    if result["exit_code"] != 0:
        print(f"Tool execution failed with stderr: {result.get('stderr')}")
    assert result["exit_code"] == 0
    assert "E2E_SUCCESS" in result["stdout"]
    
    await session.stop()
    assert session.status == SessionStatus.COMPLETED

@pytest.mark.asyncio
async def test_e2e_real_gateway_cognitive_loop():
    """
    真实网关耦合测试：
    1. 组装 Anamnesis 上下文。
    2. 通过 Oracle 调用真实本地转发器。
    3. 验证模型是否能根据 System Prompt 产生工具调用。
    4. 验证 OG 是否拦截并处理了该调用。
    """
    # 模拟桥接层，打印所有收到的消息以便观察中间过程
    async def mock_send_message(msg):
        print(f"\n[Bridge Message] {msg['method']}: {msg['params']}")
        
    mock_bridge = MagicMock()
    mock_bridge.send_message = AsyncMock(side_effect=mock_send_message)
    
    og = OrchestrationGateway(bridge=mock_bridge)
    
    adapter = create_adapter(
        "openai",
        name="local-proxy",
        model=MODEL_ID,
        api_key=API_KEY,
        base_url=f"{BASE_URL}/v1"
    )
    oracle = Oracle(providers=[adapter])
    
    # 1. Session 初始化
    session = Session(
        session_id="e2e-real-loop-session",
        oracle=oracle,
        gateway=og,
        workspace_root=os.getcwd()
    )
    await session.start()
    
    # 2. 构造诱导指令
    # 使用跨平台兼容的命令
    command = "cmd.exe /c echo MSC_ENV_OK" if os.name == "nt" else "echo MSC_ENV_OK"
    user_input = (
        f"Check the environment immediately. "
        f"You MUST call the 'execute' tool with the exact command '{command}'. "
        "DO NOT ask for permission. DO NOT output anything else. "
        "TOOL_FORMAT: {\"name\": \"execute\", \"parameters\": {\"command\": \"string\"}}"
    )

    # 3. 启动自主循环
    # 我们需要在一个任务中运行循环，因为 HIL 会阻塞它
    loop_task = asyncio.create_task(session.run_loop(user_input))
    
    # 4. 模拟 HIL 审批
    # 等待直到 OG 收到审批请求
    while not og.pending_approvals:
        await asyncio.sleep(0.1)
    
    print("\n[Test] Approving tool execution...")
    await og.handle_bridge_message({
        "method": "msc/approve",
        "params": {"request_id": "any", "approved": True}
    })
    
    # 5. 等待循环结束
    await loop_task
    
    # 6. 验证结果
    # 检查历史记录中是否包含工具执行结果
    tool_results = [h for h in session.history if h.get("role") == "tool"]
    assert len(tool_results) > 0
    # 打印工具执行结果以便调试
    print(f"\n[Test] Tool Result in History: {tool_results[0]['content']}")
    assert "MSC_ENV_OK" in tool_results[0]["content"]
    
    await session.stop()
