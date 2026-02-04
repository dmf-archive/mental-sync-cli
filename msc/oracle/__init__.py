from typing import List, Optional, Protocol, runtime_checkable, Any
from pydantic import BaseModel

@runtime_checkable
class ModelCapability(Protocol):
    has_vision: bool
    has_thinking: bool

@runtime_checkable
class ChatProvider(Protocol):
    name: str
    model_name: str
    capabilities: List[str]
    model_info: ModelCapability
    async def generate(self, prompt: str, image: Optional[str] = None) -> str: ...

class Oracle:
    def __init__(self, providers: List[ChatProvider]):
        """
        Oracle 核心类，负责 Model/Provider Free 的路由与故障转移。
        这里的 providers 列表顺序即为隐式优先级顺序。
        """
        self.providers = providers

    async def generate(
        self, 
        model_name: str, 
        prompt: str, 
        image: Optional[str] = None,
        require_caps: Optional[List[str]] = None,
        require_thinking: bool = False
    ) -> str:
        # 1. 筛选符合条件的候选者
        candidates = []
        for p in self.providers:
            if p.model_name != model_name:
                continue
            
            # 验证能力标签 (如 green-tea)
            if require_caps:
                if not all(cap in p.capabilities for cap in require_caps):
                    continue
            
            # 验证多模态支持
            if image and not p.model_info.has_vision:
                continue
            
            # 验证 CoT 支持
            if require_thinking and not p.model_info.has_thinking:
                continue
                
            candidates.append(p)

        if not candidates:
            raise ValueError(f"No provider found for {model_name}")

        # 2. 顺序尝试 (故障转移)
        last_exception = None
        for provider in candidates:
            try:
                return await provider.generate(prompt, image=image)
            except Exception as e:
                last_exception = e
                continue
        
        raise last_exception if last_exception else RuntimeError("All providers failed")

def create_adapter(provider_type: str, **kwargs: Any) -> ChatProvider:
    """
    工厂函数：根据类型创建对应的 Provider 适配器。
    """
    if provider_type == "openai":
        from msc.oracle.adapters.openai import OpenAIAdapter
        return OpenAIAdapter(**kwargs)
    elif provider_type == "anthropic":
        from msc.oracle.adapters.anthropic import AnthropicAdapter
        return AnthropicAdapter(**kwargs)
    elif provider_type == "gemini":
        from msc.oracle.adapters.gemini import GeminiAdapter
        return GeminiAdapter(**kwargs)
    elif provider_type == "ollama":
        from msc.oracle.adapters.ollama import OllamaAdapter
        return OllamaAdapter(**kwargs)
    elif provider_type == "openrouter":
        from msc.oracle.adapters.openrouter import OpenRouterAdapter
        return OpenRouterAdapter(**kwargs)
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")
