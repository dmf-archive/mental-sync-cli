from typing import Any

from msc.oracle.adapters.openai import OpenAIAdapter


class OllamaAdapter(OpenAIAdapter):
    def __init__(
        self, 
        name: str, 
        model: str, 
        api_key: str = "ollama", 
        base_url: str | None = None,
        capabilities: list[str] = None,
        has_vision: bool = False,
        has_thinking: bool = False,
        **kwargs: Any
    ):
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
