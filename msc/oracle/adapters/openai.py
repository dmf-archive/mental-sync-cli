import json
from typing import List, Optional, Any
from openai import AsyncOpenAI
from msc.oracle import ModelCapability

class OpenAIAdapter:
    """
    适配 OpenAI 兼容格式的 Provider (包括 DeepSeek, Groq, Ollama)。
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
        **kwargs: Any
    ):
        self.name = name
        self.model_name = model
        self.capabilities = capabilities or []
        self.model_info = MagicModelInfo(has_vision, has_thinking)
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, **kwargs)

    async def generate(self, prompt: str, image: Optional[str] = None) -> str:
        content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image and self.model_info.has_vision:
            content.append({
                "type": "image_url",
                "image_url": {"url": image}
            })

        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": content}],
            stream=False
        )
        return response.choices[0].message.content or ""

class MagicModelInfo:
    def __init__(self, has_vision: bool, has_thinking: bool):
        self.has_vision = has_vision
        self.has_thinking = has_thinking
