import pytest
from unittest.mock import AsyncMock, MagicMock
from msc.oracle import Oracle, ChatProvider, ModelCapability

class MockProvider:
    def __init__(self, name, model_name, fail_count=0, capabilities=None):
        self._name = name
        self._model_name = model_name
        self.fail_count = fail_count
        self.current_fails = 0
        self._capabilities = capabilities or []
        self._model_info = MagicMock(spec=ModelCapability)
        self._model_info.has_vision = "vision" in self._capabilities
        self._model_info.has_thinking = "thinking" in self._capabilities
        self._model_info.has_tools = "tool" in self._capabilities
        self._pricing = {"input_1m": 0.1, "output_1m": 0.2}

    @property
    def name(self): return self._name
    @property
    def model_name(self): return self._model_name
    @property
    def capabilities(self): return self._capabilities
    @property
    def model_info(self): return self._model_info
    @property
    def pricing(self): return self._pricing

    async def generate(self, prompt, image=None):
        if self.current_fails < self.fail_count:
            self.current_fails += 1
            raise RuntimeError(f"Provider {self.name} failed")
        return f"Response from {self.name}", [], {"input_tokens": 10, "output_tokens": 5}

@pytest.mark.asyncio
async def test_oracle_failover_mechanism():
    """
    验证 Oracle 的故障转移机制：
    1. 第一个 Provider 失败，自动尝试第二个
    2. 所有 Provider 失败，抛出异常
    """
    p1 = MockProvider("p1", "gpt-4", fail_count=1)
    p2 = MockProvider("p2", "gpt-4", fail_count=0)
    
    oracle = Oracle(providers=[p1, p2])
    
    text, _, _, provider = await oracle.generate(model_name="gpt-4", prompt="Hello")
    
    assert text == "Response from p2"
    assert provider.name == "p2"
    assert p1.current_fails == 1

@pytest.mark.asyncio
async def test_oracle_capability_routing():
    """
    验证 Oracle 根据能力标签进行路由：
    1. 只有具备 'green-tea' 标签的 Provider 才能被选中
    2. 只有具备 vision 能力的 Provider 才能处理图像
    """
    p_normal = MockProvider("normal", "gpt-4", capabilities=[])
    p_secure = MockProvider("secure", "gpt-4", capabilities=["green-tea"])
    p_vision = MockProvider("vision", "gpt-4", capabilities=["vision"])
    
    oracle = Oracle(providers=[p_normal, p_secure, p_vision])
    
    # 测试安全路由
    _, _, _, provider = await oracle.generate(model_name="gpt-4", prompt="Secret", require_caps=["green-tea"])
    assert provider.name == "secure"
    
    # 测试视觉路由
    _, _, _, provider = await oracle.generate(model_name="gpt-4", prompt="Look", image="data:image/png;base64,xxx")
    assert provider.name == "vision"

@pytest.mark.asyncio
async def test_oracle_no_matching_provider():
    """
    验证当没有匹配的 Provider 时抛出 ValueError
    """
    p1 = MockProvider("p1", "gpt-4")
    oracle = Oracle(providers=[p1])
    
    with pytest.raises(ValueError, match="No provider found for gpt-5"):
        await oracle.generate(model_name="gpt-5", prompt="Hi")
