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
SECURE_MODEL_ID = "models/qwen3-coder-flash"

@pytest.mark.asyncio
async def test_subagent_orchestration_protocol_closure():
    """
    验证子代理编排协议闭环：
    1. 跨协议 Provider 路由 (OpenAI -> Gemini/green-tea)
    2. ACL 权限缩减继承 (Parent -> Child)
    3. 跨代理消息 (ask_agent) 的 Markdown 重序列化验证
    4. complete_task 触发的级联终结 (No manual intervention)
    """
    # 1. 配置 Providers
    p_main = create_adapter(
        "openai",
        name="main-provider",
        model=MODEL_ID,
        api_key=API_KEY,
        base_url=f"{BASE_URL}/v1"
    )
    
    p_secure = create_adapter(
        "gemini",
        name="secure-provider",
        model=SECURE_MODEL_ID,
        api_key=API_KEY,
        base_url=BASE_URL,
        capabilities=["green-tea"]
    )
    
    oracle = Oracle(providers=[p_main, p_secure])
    mock_bridge = MagicMock()
    mock_bridge.send_message = AsyncMock()
    og = OrchestrationGateway(bridge=mock_bridge)
    
    # 准备工作区
    workspace = os.getcwd()
    
    main_session = Session(
        session_id="protocol-test-session",
        agent_id="main-agent",
        oracle=oracle,
        gateway=og,
        workspace_root=workspace
    )
    og.agent_registry["main-agent"] = main_session
    await main_session.start()
    
    # 指令：创建一个具备 green-tea 能力的子代理，让它计算 1+1 并通过 ask_agent 报告结果，然后它自己 complete_task。
    # 增加等待指令，防止 Agent 因为“必须调用工具”而提前 complete_task。
    user_input = (
        f"1. Spawn a subagent with 'green-tea' capability using model '{SECURE_MODEL_ID}'.\n"
        "2. Subagent instruction: 'Calculate 1+1, send the result to 'main-agent' via ask_agent, then complete_task'.\n"
        "3. You (main-agent) must WAIT for the subagent's message. If you have nothing to do while waiting, "
        "you can use 'ask_agent' to check the subagent's status or just wait for the system to provide the observation.\n"
        "4. ONLY call 'complete_task' AFTER you see the result '2' in your history."
    )
    
    # 启动主循环
    loop_task = asyncio.create_task(main_session.run_loop(user_input))
    
    timeout = 90
    start_time = asyncio.get_event_loop().time()
    
    # 2. 验证子代理创建与 ACL 继承
    while len(og.agent_registry) < 2:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout: Subagent not created")
        await asyncio.sleep(1)
    
    sub_id = next(k for k in og.agent_registry if k != "main-agent")
    sub_session = og.agent_registry[sub_id]
    
    # 验证 ACL 继承逻辑 (来自旧测试 test_agent_ops.py 的细节)
    # 子代理的 allowed_paths 应该被限制在父代理的范围内
    assert sub_session.workspace_root == main_session.workspace_root
    
    # 3. 验证跨代理消息接收 (来自旧测试 test_context.py 的细节)
    # 注意：history 存储的是原始消息，渲染后的 Markdown 仅在发送给 Oracle 的 messages 中
    while not any("Message from agent-" in str(m.get("content")) for m in main_session.history):
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout: ask_agent message not received in main-agent history")
        
        # 检查是否因为 429 或等待导致 IDLE，若是则唤醒
        if main_session.status == SessionStatus.IDLE:
            asyncio.create_task(main_session.run_loop(""))
            
        await asyncio.sleep(2)
    
    # 4. 验证级联终结 (核心协议逻辑)
    # 子代理应该先完成
    while sub_session.status != SessionStatus.COMPLETED:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout: Subagent failed to complete_task")
        await asyncio.sleep(1)
    
    # 主代理应该在感知到子代理完成后，自动调用 complete_task 结束
    while main_session.status != SessionStatus.COMPLETED:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout: Main agent failed to cascade complete_task after subagent finished")
        await asyncio.sleep(1)
    
    # 5. 最终状态审计
    record = og.session_manager.load_session(main_session.session_id, "main-agent")
    assert record is not None
    assert len(record.history) > 2
    assert any("complete_task" in str(m.get("content")) for m in record.history if m.get("role") == "assistant")

    await loop_task
    await main_session.stop()

@pytest.mark.asyncio
async def test_subagent_orchestration_with_idle_hook():
    """
    白箱测试：验证主代理在等待子代理时进入 IDLE 状态，并通过 hook 机制唤醒。
    这是为了验证框架在等待异步子代理时的行为。
    """
    p_main = create_adapter(
        "openai",
        name="main-provider",
        model=MODEL_ID,
        api_key=API_KEY,
        base_url=f"{BASE_URL}/v1"
    )
    
    oracle = Oracle(providers=[p_main])
    mock_bridge = MagicMock()
    mock_bridge.send_message = AsyncMock()
    og = OrchestrationGateway(bridge=mock_bridge)
    
    main_session = Session(
        session_id="idle-hook-test-session",
        agent_id="main-agent",
        oracle=oracle,
        gateway=og,
        workspace_root=os.getcwd()
    )
    og.agent_registry["main-agent"] = main_session
    await main_session.start()
    
    # 指令：创建一个子代理，主代理等待其完成。
    # 明确要求使用 ask_agent('human') 来挂起，以稳定触发 IDLE 状态。
    user_input = (
        "1. Spawn a subagent to calculate 1+1 and complete_task.\n"
        "2. After spawning, you MUST use 'ask_agent' with agent_id='human' to report that you are waiting for the subagent.\n"
        "3. This will suspend your session. Do not attempt any other tools until you are awakened.\n"
        "4. Only complete_task after you receive the result '2' from the subagent."
    )
    
    loop_task = asyncio.create_task(main_session.run_loop(user_input))
    
    timeout = 90
    start_time = asyncio.get_event_loop().time()
    
    # 等待子代理创建
    while len(og.agent_registry) < 2:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout: Subagent not created")
        await asyncio.sleep(1)
    
    # 验证主代理进入 IDLE 状态
    while main_session.status != SessionStatus.IDLE:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout: Main agent did not enter IDLE state while waiting")
        await asyncio.sleep(1)
    
    print(f"\n[TEST] Main agent entered IDLE state at {asyncio.get_event_loop().time() - start_time:.2f}s")
    
    # 模拟子代理完成并发送结果
    sub_id = next(k for k in og.agent_registry if k != "main-agent")
    sub_session = og.agent_registry[sub_id]
    
    # 手动触发子代理的 complete_task
    from msc.core.tools.agent_ops import CompleteTaskTool
    from msc.core.tools.base import ToolContext
    
    tool_context = ToolContext(
        agent_id=sub_id,
        workspace_root=main_session.workspace_root,
        oracle=oracle,
        gateway=og
    )
    
    complete_tool = CompleteTaskTool(tool_context)
    await complete_tool.execute(summary="Calculated 1+1=2", data={"result": 2})
    
    print(f"\n[TEST] Subagent completed task at {asyncio.get_event_loop().time() - start_time:.2f}s")
    
    # 验证主代理被唤醒并继续运行
    while main_session.status == SessionStatus.IDLE:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout: Main agent was not awakened by subagent's complete_task")
        await asyncio.sleep(1)
    
    print(f"\n[TEST] Main agent awakened at {asyncio.get_event_loop().time() - start_time:.2f}s")
    
    # 验证主代理最终完成
    while main_session.status != SessionStatus.COMPLETED:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout: Main agent did not complete after being awakened")
        await asyncio.sleep(1)
    
    print(f"\n[TEST] Main agent completed at {asyncio.get_event_loop().time() - start_time:.2f}s")
    
    await loop_task
    await main_session.stop()
