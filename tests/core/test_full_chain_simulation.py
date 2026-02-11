import asyncio
import os
import shutil
import pytest
from unittest.mock import AsyncMock, MagicMock
from msc.core.og import OrchestrationGateway, Session, SessionStatus
from msc.oracle import Oracle, create_adapter

# 本地转发器配置
BASE_URL = "http://localhost:8317"
API_KEY = "123456"
MODEL_ID = "gemini-2.5-flash-lite"

@pytest.fixture
def mock_workspace(tmp_path):
    """创建模拟工作区，包含 src 目录和初始文件"""
    workspace = tmp_path / "mock_workspace"
    workspace.mkdir()
    src_dir = workspace / "src"
    src_dir.mkdir()
    main_py = src_dir / "main.py"
    # 初始内容包含 hello，用于验证修改
    main_py.write_text("def hello():\n    print('hello')\n", encoding="utf-8")
    
    # 预置项目规则文件，验证 RulesDiscoverer (来自旧测试 test_discover.py)
    rules_dir = workspace / ".msc" / "rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "coding_std.md").write_text("#### REQ-101\nCode must be self-explanatory.\n", encoding="utf-8")
    
    # 预置 Notebook，引导模型使用 execute 来读取文件 (来自 MSC 协议设计)
    notebook_dir = workspace / ".msc" / "notebook"
    notebook_dir.mkdir(parents=True)
    notebook_content = """## CLI Tooling Guide
- `read_file` is NOT available.
- To read file content, use `execute` with `type <path>` (Windows) or `cat <path>` (Linux).
- Always verify file content before using `apply_diff`.
"""
    (notebook_dir / "memory-1.md").write_text(notebook_content, encoding="utf-8")

    return workspace

@pytest.mark.asyncio
async def test_full_chain_simulation_with_conflict_resolution(mock_workspace):
    """
    全链路仿真测试（含冲突处理与规则发现）：
    1. 验证 RulesDiscoverer 自动加载项目规则。
    2. Main Agent 派生子代理执行文件修改任务。
    3. 子代理必须使用 apply_diff 且成功修改文件内容。
    4. 验证级联终结协议：子代理 complete_task -> 主代理感知 -> 主代理 complete_task。
    """
    # 强制清除可能干扰本地连接的代理环境变量，并设置 NO_PROXY
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)
    os.environ.pop("ALL_PROXY", None)

    p_openai = create_adapter(
        "openai",
        name="local-openai",
        model=MODEL_ID,
        api_key=API_KEY,
        base_url=f"{BASE_URL}/v1",
        pricing={"input_1m": 0.1, "output_1m": 0.2}
    )
    oracle = Oracle(providers=[p_openai])
    
    mock_bridge = MagicMock()
    mock_bridge.send_message = AsyncMock()
    
    og = OrchestrationGateway(bridge=mock_bridge)
    
    main_session = Session(
        session_id="full-chain-sim-v3",
        agent_id="main-agent",
        oracle=oracle,
        gateway=og,
        workspace_root=str(mock_workspace)
    )
    og.agent_registry["main-agent"] = main_session
    await main_session.start()
    
    # 验证规则发现 (REQ-101 应出现在上下文组装中)
    rules_dict = main_session.rules_discoverer.scan()
    assert any("REQ-101" in content for content in rules_dict.values())
    
    # 指令要求子代理修改文件，并要求主代理在确认修改后结束
    # 增加工具使用指引，确保 Agent 知道如何查看文件内容
    user_input = (
        "1. Use 'create_agent' to delegate the task: change 'hello' to 'world' in src/main.py using 'apply_diff'.\n"
        "2. IMPORTANT: If the subagent needs to see the file content, tell it to use 'execute' with 'type src/main.py'.\n"
        "3. You must wait for the subagent to report its result via 'complete_task'.\n"
        "4. Do not complete your own task until you have confirmed the file content has changed to 'world'.\n"
        "5. While waiting, use 'ask_agent' with agent_id='human' to suspend if you have no other actions."
    )
    
    loop_task = asyncio.create_task(main_session.run_loop(user_input))
    
    timeout = 120
    start_time = asyncio.get_event_loop().time()
    
    # 1. 等待子代理注册
    while len(og.agent_registry) < 2:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout: Subagent registration failed")
        await asyncio.sleep(1)
    
    sub_id = next(k for k in og.agent_registry if k != "main-agent")
    sub_session = og.agent_registry[sub_id]
    
    # 2. 轮询文件内容，验证修改已生效 (来自旧测试 test_minimal_tools.py)
    target_file = mock_workspace / "src" / "main.py"
    while "world" not in target_file.read_text(encoding="utf-8"):
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout: File content was not modified by subagent")
        await asyncio.sleep(1)
    
    # 3. 验证级联终结 (核心协议：子代理完成 -> 主代理感知 -> 主代理完成)
    while sub_session.status != SessionStatus.COMPLETED:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout: Subagent did not call complete_task")
        await asyncio.sleep(1)
        
    while main_session.status != SessionStatus.COMPLETED:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail("Timeout: Main agent did not cascade complete_task after subagent finished")
        await asyncio.sleep(1)
    
    # 4. 最终状态审计
    assert "world" in target_file.read_text()
    # 验证主代理历史中包含子代理的原始汇报负载 (history 存储原始数据)
    assert any("task_result" in str(m.get("content")) for m in main_session.history)
    
    await loop_task
    await main_session.stop()
