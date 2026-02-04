from msc.core.anamnesis.metadata import MetadataProvider
from msc.core.anamnesis.types import SessionMetadata


def test_metadata_provider_collects_real_data():
    provider = MetadataProvider(agent_id="test-agent")
    metadata = provider.collect()
    
    assert isinstance(metadata, SessionMetadata)
    assert metadata.agent_id == "test-agent"
    assert metadata.workspace_root != ""
    assert isinstance(metadata.active_terminals, list)
    # 验证时间格式是否符合 ISO 8601
    assert metadata.start_time.isoformat() != ""

def test_metadata_provider_includes_pfms_status():
    provider = MetadataProvider(agent_id="test-agent")
    # 模拟 PFMS 状态注入
    provider.set_pfms_status(model_name="claude-3.5-sonnet", cost={"input": 0.003, "output": 0.015})
    metadata = provider.collect()
    
    assert metadata.model_name == "claude-3.5-sonnet"
    assert metadata.provider_cost["input"] == 0.003
