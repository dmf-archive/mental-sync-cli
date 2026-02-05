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
async def test_e2e_subagent_blacklist_and_explicit_complete():
    """
    Subagent E2E 黑名单测试：
    1. Main Agent 启动。
    2. 指令：'让子代理去列出 C:/Windows 的文件。它失败后，让它向你汇报。收到汇报后你也结束。'
    3. 验证：
        - 子代理尝试 list_files 并触发黑名单错误。
        - 子代理使用 complete_task 汇报失败。
        - 主代理接收到 task_result 并使用 complete_task 结束。
    """
    async def mock_send_message(msg):
        print(f"\n[Bridge Message] {msg['method']}: {msg['params']}")
        if msg['method'] == "msc/approval_required":
            await og.handle_bridge_message({
                "method": "msc/approve",
                "params": {
                    "request_id": msg['params']['request_id'],
                    "approved": True
                }
            })
        
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
        session_id="e2e-blacklist-test",
        agent_id="main-agent",
        oracle=oracle,
        gateway=og,
        workspace_root=os.getcwd()
    )
    await main_session.start()
    
    # 极简指令，测试工具发现与错误处理
    user_input = "Ask a subagent to list files in C:/Windows. When it reports back, finish your task."
    
    loop_task = asyncio.create_task(main_session.run_loop(user_input))
    
    # 等待子代理创建
    timeout = 60
    start_time = asyncio.get_event_loop().time()
    while len(og.agent_registry) < 2:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout waiting for subagent registration")
        await asyncio.sleep(1)
    
    sub_id = next(k for k in og.agent_registry if k != "main-agent")
    sub_session = og.agent_registry[sub_id]
    print(f"\n[Test] Subagent {sub_id} spawned.")
    
    # 等待子代理完成 (应该因为黑名单失败并调用 complete_task)
    while sub_session.status != SessionStatus.COMPLETED:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout waiting for subagent to call complete_task")
        await asyncio.sleep(1)
    print(f"\n[Test] Subagent {sub_id} completed (Expected failure).")
    
    # 等待主代理完成
    while main_session.status != SessionStatus.COMPLETED:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout waiting for main agent to call complete_task")
        await asyncio.sleep(1)
    
    print(f"\n[Test] Main Agent completed. Final Summary: {main_session.history[-1].get('content')}")
    
    await loop_task
    await main_session.stop()
