from typing import List, Optional, Any
from anthropic import AsyncAnthropic
from msc.oracle import ModelCapability

class AnthropicAdapter:
    """
    适配 Anthropic 原生格式的 Provider。
    """
    def __init__(
        self, 
        name: str, 
        model: str, 
        api_key: str, 
        base_url: Optional[str] = None,
        capabilities: List[str] = None,
        has_vision: bool = False,
        has_thinking: bool = False,
        default_max_tokens: int = 4096,
        **kwargs: Any
    ):
        self.name = name
        self.model_name = model
        self.capabilities = capabilities or []
        self.model_info = MagicModelInfo(has_vision, has_thinking)
        self.default_max_tokens = default_max_tokens
        self.client = AsyncAnthropic(api_key=api_key, base_url=base_url, **kwargs)

    async def generate(self, prompt: str, image: Optional[str] = None) -> str:
        content = []
        if image and self.model_info.has_vision:
            # Anthropic expects base64 data for images in a specific format
            # For simplicity in this adapter, we assume the image string is handled
            # or we'd need a more complex parser like in kosong
            pass
        
        content.append({"type": "text", "text": prompt})

        response = await self.client.messages.create(
            model=self.model_name,
            max_tokens=self.default_max_tokens,
            messages=[{"role": "user", "content": content}],
            stream=False
        )
        # Anthropic response content is a list of blocks
        text_content = "".join([block.text for block in response.content if block.type == "text"])
        return text_content

class MagicModelInfo:
    def __init__(self, has_vision: bool, has_thinking: bool):
        self.has_vision = has_vision
        self.has_thinking = has_thinking
