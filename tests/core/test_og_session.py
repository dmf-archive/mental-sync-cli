import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

# 假设我们将 OG 核心逻辑放在 msc.core.og 中
from msc.core.og import Session, SessionStatus, OrchestrationGateway

@pytest.mark.asyncio
async def test_session_lifecycle_management():
    """
    RED Phase: 测试 Session 的生命周期管理。
    预期失败：ImportError 或 NameError。
    """
    # 模拟依赖
    mock_oracle = MagicMock()
    workspace_root = "/tmp/msc-test"
    
    # 创建 Session
    session = Session(
        session_id="test-session",
        oracle=mock_oracle,
        workspace_root=workspace_root
    )
    
    # 初始状态应为 IDLE
    assert session.status == SessionStatus.IDLE
    
    # 启动 Session
    await session.start()
    assert session.status == SessionStatus.RUNNING
    
    # 停止 Session
    await session.stop()
    assert session.status == SessionStatus.COMPLETED

@pytest.mark.asyncio
async def test_og_permission_request_blocking():
    """
    RED Phase: 测试 OG 的权限请求阻塞机制 (HIL)。
    预期失败：NameError。
    """
    mock_bridge = AsyncMock()
    og = OrchestrationGateway(bridge=mock_bridge)
    
    # 模拟一个权限请求
    # 启动一个任务来请求权限
    request_task = asyncio.create_task(
        og.request_permission(
            agent_id="agent-1",
            action="execute",
            params={"command": "rm -rf /"}
        )
    )
    
    # 验证请求是否已发送到桥接层
    await asyncio.sleep(0.1)
    mock_bridge.send_message.assert_called()
    
    # 模拟用户通过桥接层批准
    await og.handle_bridge_message({
        "method": "msc/approve",
        "params": {"request_id": "any", "approved": True}
    })
    
    # 验证任务是否恢复并返回 True
    result = await request_task
    assert result is True
