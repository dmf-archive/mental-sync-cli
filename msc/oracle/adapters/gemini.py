from typing import Any

from google import genai
from google.genai import types


class GeminiAdapter:
    def __init__(
        self, 
        name: str, 
        model: str, 
        api_key: str, 
        base_url: str | None = None,
        capabilities: list[str] = None,
        has_vision: bool = False,
        has_thinking: bool = False,
        vertexai: bool = False,
        **kwargs: Any
    ):
        self.name = name
        self.model_name = model
        self.capabilities = capabilities or []
        self.model_info = MagicModelInfo(has_vision, has_thinking)
        
        http_options = types.HttpOptions(base_url=base_url) if base_url else None
        self.client = genai.Client(
            api_key=api_key,
            vertexai=vertexai,
            http_options=http_options,
            **kwargs
        )

    async def generate(self, prompt: str, image: str | None = None) -> str:
        contents = []
        parts = [types.Part.from_text(text=prompt)]
        
        if image and self.model_info.has_vision:
            pass
            
        contents.append(types.Content(role="user", parts=parts))

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(include_thoughts=True) if self.model_info.has_thinking else None
            )
        )
        
        return response.text or ""

class MagicModelInfo:
    def __init__(self, has_vision: bool, has_thinking: bool):
        self.has_vision = has_vision
        self.has_thinking = has_thinking
