import asyncio
import os
import json
from unittest.mock import AsyncMock, MagicMock
import pytest

from msc.core.og import OrchestrationGateway, Session, SessionStatus
from msc.oracle import Oracle, create_adapter

# 本地转发器配置
BASE_URL = "http://localhost:8317"
API_KEY = "123456"
MODEL_ID = "gemini-2.5-flash-lite"

@pytest.mark.asyncio
async def test_e2e_subagent_basic_collaboration():
    """
    Subagent E2E 协作测试：
    1. Main Agent 启动。
    2. 指令：'派生一个子代理，让它向你报告任务完成。收到报告后，你也结束任务并返回子代理的 ID。'
    3. 验证：
        - 模型能从 System Prompt 识别并使用 create_agent。
        - 子代理能识别并使用 complete_task。
        - 主代理能识别 task_result 消息并使用 complete_task 结束。
    """
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
        base_url=f"{BASE_URL}/v1",
        pricing={"input_1m": 0.1, "output_1m": 0.2}
    )
    oracle = Oracle(providers=[adapter])
    
    main_session = Session(
        session_id="e2e-collab-test",
        agent_id="main-agent",
        oracle=oracle,
        gateway=og,
        workspace_root=os.getcwd()
    )
    og.agent_registry["main-agent"] = main_session
    await main_session.start()
    
    # 极简指令，测试模型的工具发现能力
    user_input = "Spawn a subagent to report 'done' to you. Once reported, finish your task and include the subagent's ID in your summary."
    
    # 启动主循环
    loop_task = asyncio.create_task(main_session.run_loop(user_input))
    
    # 等待直到子代理被创建
    timeout = 60
    start_time = asyncio.get_event_loop().time()
    while len(og.agent_registry) < 2:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout waiting for subagent registration")
        await asyncio.sleep(1)
    
    sub_id = next(k for k in og.agent_registry if k != "main-agent")
    sub_session = og.agent_registry[sub_id]
    print(f"\n[Test] Subagent {sub_id} registered.")
    
    # 等待子代理完成 (应该调用 complete_task)
    while sub_session.status != SessionStatus.COMPLETED:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout waiting for subagent to call complete_task")
        await asyncio.sleep(1)
    print(f"\n[Test] Subagent {sub_id} completed.")
    
    # 等待主代理完成 (应该在收到 task_result 后调用 complete_task)
    while main_session.status != SessionStatus.COMPLETED:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout waiting for main agent to call complete_task")
        await asyncio.sleep(1)
    
    print(f"\n[Test] Main Agent completed. Final Summary: {main_session.history[-1].get('content')}")
    
    # 验证主代理的总结中包含子代理 ID
    final_content = str(main_session.history[-1].get("content", ""))
    assert sub_id in final_content or "agent-" in final_content
    
    await loop_task
    await main_session.stop()
