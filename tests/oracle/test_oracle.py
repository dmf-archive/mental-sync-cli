from typing import Protocol
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

# --- 1. 核心协议与数据模型 (模拟生产环境) ---

class ModelCapability(BaseModel):
    has_vision: bool = False
    has_thinking: bool = False

class ChatProvider(Protocol):
    name: str
    model_name: str
    capabilities: list[str]
    model_info: ModelCapability
    async def generate(self, prompt: str, image: str | None = None) -> str: ...

# --- 2. 完备的 Mock 构造器 ---

def create_complex_mock_provider(
    name: str, 
    model_name: str, 
    caps: list[str], 
    has_vision: bool = False,
    has_thinking: bool = False,
    response: str = "Default Assistant Message"
):
    mock = MagicMock(spec=ChatProvider)
    mock.name = name
    mock.model_name = model_name
    mock.capabilities = caps
    mock.model_info = ModelCapability(has_vision=has_vision, has_thinking=has_thinking)
    mock.generate = AsyncMock(return_value=response)
    return mock

# --- 3. 单元测试套件 ---

@pytest.mark.asyncio
async def test_oracle_green_tea_routing():
    """验证 Green TEA 隔离性：敏感任务必须路由到受信任的 Provider"""
    from msc.oracle import Oracle
    
    p_official = create_complex_mock_provider(
        "official-anthropic", "claude-3.5-sonnet", caps=[], response="Official Response"
    )
    p_local = create_complex_mock_provider(
        "local-ollama", "claude-3.5-sonnet", caps=["green-tea"], response="Local Secure Response"
    )
    
    oracle = Oracle(providers=[p_official, p_local])
    
    # 请求需要 green-tea 能力的逻辑模型
    response = await oracle.generate("claude-3.5-sonnet", "secret task", require_caps=["green-tea"])
    
    assert response == "Local Secure Response"
    p_local.generate.assert_called_once()
    p_official.generate.assert_not_called()

@pytest.mark.asyncio
async def test_oracle_multimodal_dispatch():
    """验证多模态分发：只有具备 vision 能力的模型才能处理图片"""
    from msc.oracle import Oracle
    
    p_text = create_complex_mock_provider("text-only", "deepseek-v3", caps=[], has_vision=False)
    p_vision = create_complex_mock_provider("vision-model", "gpt-4o", caps=[], has_vision=True)
    
    oracle = Oracle(providers=[p_text, p_vision])
    
    # 尝试发送带图片的请求
    await oracle.generate("gpt-4o", "what is in this image?", image="data:image/png;base64...")
    
    p_vision.generate.assert_called_once()
    p_text.generate.assert_not_called()

def test_config_serialization_security():
    """验证序列化安全：防止任意代码执行 (ACE)"""
    malicious_yaml = """
    providers:
      - name: !!python/object/apply:os.system ["echo ACE_EXPLOITED"]
        type: openai
        api_key: "sk-..."
        models: []
    """
    
    from msc.oracle.config import load_config_safely
    
    # 应该抛出 ValueError (由 SafeLoader 拒绝解析未知 tag 引起)
    with pytest.raises(ValueError, match="YAML parsing error"):
        load_config_safely(malicious_yaml)

@pytest.mark.asyncio
async def test_oracle_cot_fallback():
    """验证 CoT (Thinking) 支持：如果首选模型不支持 Thinking，是否按顺序回退"""
    from msc.oracle import Oracle
    
    p1 = create_complex_mock_provider("fast-model", "model-x", caps=[], has_thinking=False)
    p2 = create_complex_mock_provider("thinking-model", "model-x", caps=[], has_thinking=True, response="CoT Response")
    
    oracle = Oracle(providers=[p1, p2])
    
    # 请求需要 Thinking 的任务
    response = await oracle.generate("model-x", "complex math", require_thinking=True)
    
    assert response == "CoT Response"
    p2.generate.assert_called_once()

@pytest.mark.asyncio
async def test_openrouter_pricing_refresh():
    """验证 OpenRouter 价格刷新机制：不带 Key 且正确解析"""
    from msc.oracle.adapters.openrouter import OpenRouterAdapter
    
    adapter = OpenRouterAdapter(name="or", model="anthropic/claude-3.5-sonnet", api_key="sk-test")
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "id": "anthropic/claude-3.5-sonnet",
                "pricing": {"prompt": "0.000003", "completion": "0.000015"}
            }
        ]
    }
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        await adapter.refresh_pricing()
        
        # 验证不带 Authorization
        args, kwargs = mock_get.call_args
        assert "headers" not in kwargs or "Authorization" not in kwargs.get("headers", {})
        
        # 验证价格转换 ($/1M)
        assert adapter.pricing["input_1m"] == 3.0
        assert adapter.pricing["output_1m"] == 15.0

@pytest.mark.asyncio
async def test_ollama_default_url():
    """验证 Ollama 默认 URL 逻辑"""
    from msc.oracle.adapters.ollama import OllamaAdapter
    
    adapter = OllamaAdapter(name="local", model="llama3")
    assert str(adapter.client.base_url) == "http://localhost:11434/v1/"
