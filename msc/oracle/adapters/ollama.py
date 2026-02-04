from typing import List, Optional, Any
from msc.oracle.adapters.openai import OpenAIAdapter

class OllamaAdapter(OpenAIAdapter):
    """
    专用于 Ollama 的适配器，默认指向本地地址。
    """
    def __init__(
        self, 
        name: str, 
        model: str, 
        api_key: str = "ollama", 
        base_url: Optional[str] = None,
        capabilities: List[str] = None,
        has_vision: bool = False,
        has_thinking: bool = False,
        **kwargs: Any
    ):
        # 如果 base_url 为空，默认指向本地 Ollama 服务
        # 遵循用户指令：如果 base 为空不会直接报错
        actual_base_url = base_url or "http://localhost:11434/v1"
        
        super().__init__(
            name=name,
            model=model,
            api_key=api_key,
            base_url=actual_base_url,
            capabilities=capabilities,
            has_vision=has_vision,
            has_thinking=has_thinking,
            **kwargs
        )
