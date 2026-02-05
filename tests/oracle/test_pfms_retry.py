import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from msc.oracle import Oracle, ChatProvider

class MockProvider(ChatProvider):
    def __init__(self, name, model_name, fail_count=0, error_type=Exception):
        self._name = name
        self._model_name = model_name
        self.fail_count = fail_count
        self.error_type = error_type
        self.calls = 0
        self._capabilities = []
        self._model_info = MagicMock()
        self._model_info.has_vision = True
        self._model_info.has_thinking = True

    @property
    def name(self): return self._name
    @property
    def model_name(self): return self._model_name
    @property
    def capabilities(self): return self._capabilities
    @property
    def model_info(self): return self._model_info

    async def generate(self, prompt, image=None):
        self.calls += 1
        if self.calls <= self.fail_count:
            raise self.error_type(f"Simulated failure {self.calls}")
        return f"Success from {self.name}"

@pytest.mark.asyncio
async def test_oracle_failover_on_error():
    p1 = MockProvider("p1", "gpt-4", fail_count=1)
    p2 = MockProvider("p2", "gpt-4", fail_count=0)
    
    oracle = Oracle(providers=[p1, p2])
    result = await oracle.generate(model_name="gpt-4", prompt="hello")
    
    assert result == "Success from p2"
    assert p1.calls == 1
    assert p2.calls == 1

@pytest.mark.asyncio
async def test_oracle_all_fail_raises_last_error():
    p1 = MockProvider("p1", "gpt-4", fail_count=1, error_type=ValueError)
    
    oracle = Oracle(providers=[p1])
    with pytest.raises(ValueError, match="Simulated failure 1"):
        await oracle.generate(model_name="gpt-4", prompt="hello")
