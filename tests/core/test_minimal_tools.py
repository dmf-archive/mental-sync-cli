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
async def test_minimal_toolset_functionality():
    """
    验证最小工具集的功能性：
    1. write_file: 写入测试文件
    2. list_files: 列出测试文件
    3. apply_diff: 修改测试文件
    4. memory: 模拟记忆操作
    5. model_switch: 模拟模型切换
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
    
    workspace = os.path.join(os.getcwd(), "test_workspace_tools")
    os.makedirs(workspace, exist_ok=True)
    
    main_session = Session(
        session_id="toolset-test",
        agent_id="main-agent",
        oracle=oracle,
        gateway=og,
        workspace_root=workspace
    )
    og.agent_registry["main-agent"] = main_session
    await main_session.start()
    
    # 构造一个包含所有工具调用的指令
    user_input = (
        "Perform the following sequence of actions:\n"
        "1. Use 'write_file' (path='test.txt', content='hello world') to write to a file.\n"
        "2. Use 'list_files' (path='.') to list the files.\n"
        "3. Use 'apply_diff' (path='test.txt', diff='<<<<<<< SEARCH\\nhello world\\n=======\\nhello msc\\n>>>>>>> REPLACE') to change content.\n"
        "4. Use 'memory' (action='add', key='status', message='tools verified') to record progress.\n"
        "5. Use 'model_switch' (model_name='gpt-4o') to switch model.\n"
        "6. Finally, use 'complete_task' (summary='All tools verified') to finish."
    )
    
    # 启动主循环
    loop_task = asyncio.create_task(main_session.run_loop(user_input))
    
    # 等待主代理完成
    timeout = 60
    start_time = asyncio.get_event_loop().time()
    while main_session.status != SessionStatus.COMPLETED:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout waiting for toolset verification")
        await asyncio.sleep(1)
    
    # 验证文件写入和修改
    test_file_path = os.path.join(workspace, "test.txt")
    assert os.path.exists(test_file_path)
    with open(test_file_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "hello msc" in content
    
    print(f"\n[Test] Toolset verification successful.")
    
    await loop_task
    await main_session.stop()
    
    # 清理 (已注释，以便用户检查结果)
    # import shutil
    # shutil.rmtree(workspace, ignore_errors=True)
